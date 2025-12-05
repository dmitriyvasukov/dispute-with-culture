from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import (
    CartWithProductsResponse,
    CartItemCreate,
    CartItemUpdate,
    CartItemWithProductResponse
)

router = APIRouter()


def get_or_create_cart(user_id: int, db: Session) -> Cart:
    """Получить или создать корзину для пользователя"""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.get("/", response_model=CartWithProductsResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить корзину текущего пользователя
    """
    cart = db.query(Cart).options(
        joinedload(Cart.items).joinedload(CartItem.product)
    ).filter(Cart.user_id == current_user.id).first()

    if not cart:
        # Создать корзину в БД
        cart = get_or_create_cart(current_user.id, db)

    # Рассчитать итоги
    total_items = sum(item.quantity for item in cart.items)
    total_amount = sum(item.quantity * item.product.price for item in cart.items)

    # Подготовить данные для ответа
    response_data = {
        "id": cart.id,
        "user_id": cart.user_id,
        "created_at": cart.created_at,
        "updated_at": cart.updated_at,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "size": item.size,
                "quantity": item.quantity,
                "created_at": item.created_at,
                "product_name": item.product.name,
                "product_price": item.product.price,
                "product_article": item.product.article,
                "product": {
                    "id": item.product.id,
                    "name": item.product.name,
                    "description": item.product.description,
                    "article": item.product.article,
                    "price": item.product.price,
                    "sizes": item.product.sizes,
                    "size_table": item.product.size_table,
                    "care_instructions": item.product.care_instructions,
                    "preview_image_url": item.product.preview_image_url,
                    "order_type": item.product.order_type.value,
                    "stock_count": item.product.stock_count,
                    "preorder_waves_total": item.product.preorder_waves_total,
                    "preorder_wave_capacity": item.product.preorder_wave_capacity,
                    "current_wave": item.product.current_wave,
                    "current_wave_count": item.product.current_wave_count,
                    "is_active": item.product.is_active,
                    "is_archived": item.product.is_archived,
                    "created_at": item.product.created_at,
                    "updated_at": item.product.updated_at,
                    "media": [
                        {
                            "url": media.url,
                            "order": media.order,
                            "id": media.id,
                            "created_at": media.created_at
                        } for media in item.product.media
                    ]
                }
            } for item in cart.items
        ],
        "total_items": total_items,
        "total_amount": total_amount
    }

    return CartWithProductsResponse(**response_data)


@router.post("/items", response_model=CartItemWithProductResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    item_data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Добавить товар в корзину
    """
    # Проверить продукт
    product = db.query(Product).filter(Product.id == item_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Товар недоступен"
        )

    # Проверить размер (для предзаказов размер может быть 'PREORDER')
    if product.order_type.value != 'preorder' and item_data.size not in product.sizes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Размер {item_data.size} недоступен для этого товара"
        )

    # Проверить количество (для предзаказов не проверяем)
    if product.order_type.value != 'preorder' and product.sizes.get(item_data.size, 0) < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недостаточно товара размера {item_data.size} на складе"
        )

    # Получить или создать корзину
    cart = get_or_create_cart(current_user.id, db)

    # Проверить, есть ли уже такой товар в корзине
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item_data.product_id,
        CartItem.size == item_data.size
    ).first()

    if existing_item:
        # Обновить количество
        existing_item.quantity += item_data.quantity
        db.commit()
        db.refresh(existing_item)
        item = existing_item
    else:
        # Создать новый элемент
        item = CartItem(
            cart_id=cart.id,
            product_id=item_data.product_id,
            size=item_data.size,
            quantity=item_data.quantity
        )
        db.add(item)
        db.commit()
        db.refresh(item)

    # Подготовить данные для ответа
    response_data = {
        "id": item.id,
        "product_id": item.product_id,
        "size": item.size,
        "quantity": item.quantity,
        "created_at": item.created_at,
        "product_name": product.name,
        "product_price": product.price,
        "product_article": product.article,
        "product": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "article": product.article,
            "price": product.price,
            "sizes": product.sizes,
            "size_table": product.size_table,
            "care_instructions": product.care_instructions,
            "preview_image_url": product.preview_image_url,
            "order_type": product.order_type.value,
            "stock_count": product.stock_count,
            "preorder_waves_total": product.preorder_waves_total,
            "preorder_wave_capacity": product.preorder_wave_capacity,
            "current_wave": product.current_wave,
            "current_wave_count": product.current_wave_count,
            "is_active": product.is_active,
            "is_archived": product.is_archived,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "media": [
                {
                    "url": media.url,
                    "order": media.order,
                    "id": media.id,
                    "created_at": media.created_at
                } for media in product.media
            ]
        }
    }

    return CartItemWithProductResponse(**response_data)


@router.put("/items/{item_id}", response_model=CartItemWithProductResponse)
async def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновить количество товара в корзине
    """
    item = db.query(CartItem).options(
        joinedload(CartItem.cart),
        joinedload(CartItem.product)
    ).filter(CartItem.id == item_id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Элемент корзины не найден"
        )

    # Проверить, что корзина принадлежит пользователю
    if item.cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    item.quantity = item_data.quantity
    db.commit()
    db.refresh(item)

    # Подготовить данные для ответа
    response_data = {
        "id": item.id,
        "product_id": item.product_id,
        "size": item.size,
        "quantity": item.quantity,
        "created_at": item.created_at,
        "product_name": item.product.name,
        "product_price": item.product.price,
        "product_article": item.product.article,
        "product": {
            "id": item.product.id,
            "name": item.product.name,
            "description": item.product.description,
            "article": item.product.article,
            "price": item.product.price,
            "sizes": item.product.sizes,
            "size_table": item.product.size_table,
            "care_instructions": item.product.care_instructions,
            "preview_image_url": item.product.preview_image_url,
            "order_type": item.product.order_type.value,
            "stock_count": item.product.stock_count,
            "preorder_waves_total": item.product.preorder_waves_total,
            "preorder_wave_capacity": item.product.preorder_wave_capacity,
            "current_wave": item.product.current_wave,
            "current_wave_count": item.product.current_wave_count,
            "is_active": item.product.is_active,
            "is_archived": item.product.is_archived,
            "created_at": item.product.created_at,
            "updated_at": item.product.updated_at,
            "media": [
                {
                    "url": media.url,
                    "order": media.order,
                    "id": media.id,
                    "created_at": media.created_at
                } for media in item.product.media
            ]
        }
    }

    return CartItemWithProductResponse(**response_data)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Удалить товар из корзины
    """
    item = db.query(CartItem).options(
        joinedload(CartItem.cart)
    ).filter(CartItem.id == item_id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Элемент корзины не найден"
        )

    # Проверить, что корзина принадлежит пользователю
    if item.cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    db.delete(item)
    db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Очистить корзину
    """
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if cart:
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.commit()