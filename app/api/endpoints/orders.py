from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, OrderType
from app.models.promo_code import PromoCode
from app.models.cart import Cart, CartItem
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse, BulkPreorderStatusUpdate

router = APIRouter()


@router.get("/", response_model=OrderListResponse)
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить заказы текущего пользователя
    """
    from sqlalchemy.orm import joinedload
    
    query = db.query(Order).filter(Order.user_id == current_user.id)
    
    total = query.count()
    # Use eager loading to avoid N+1 problem
    orders = query.options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    return OrderListResponse(
        orders=orders,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.patch("/admin/bulk-production-status", response_model=dict)
async def bulk_update_production_status(
    product_ids: List[int],
    status: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Массово обновить статусы производства предзаказов (только для администраторов)
    """
    from app.models.product import ProductionStatus

    if not product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не указаны ID товаров"
        )

    # Проверяем, что все указанные товары существуют и являются предзаказами
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()

    if len(products) != len(product_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Один или несколько товаров не найдены"
        )

    # Проверяем, что все товары являются предзаказами
    invalid_products = []
    for product in products:
        if product.order_type != OrderType.PREORDER:
            invalid_products.append(product.name)

    if invalid_products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Товары {', '.join(invalid_products)} не являются предзаказами"
        )

    # Обновляем статусы производства
    updated_count = 0
    for product in products:
        product.production_status = ProductionStatus(status)
        updated_count += 1

    db.commit()

    return {
        "message": f"Статусы производства {updated_count} товаров успешно обновлены",
        "updated_count": updated_count
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить заказ по ID
    """
    from sqlalchemy.orm import joinedload
    
    order = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Check if user owns this order or is admin
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )
    
    return order


@router.post("/", response_model=List[OrderResponse], status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Создать новый заказ (или заказы, если есть товары с разными типами)
    """
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload

    # Получить корзину пользователя
    cart = None
    if order_data.from_cart:
        cart = db.query(Cart).options(
            joinedload(Cart.items).joinedload(CartItem.product)
        ).filter(Cart.user_id == current_user.id).first()

        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Корзина пуста"
            )

    order_items_data = []
    items_to_process = cart.items if order_data.from_cart else order_data.items

    for item_data in items_to_process:
        # Определить product_id и size в зависимости от типа item_data
        if hasattr(item_data, 'product_id'):
            # OrderItemCreate
            product_id = item_data.product_id
            size = item_data.size
            quantity = item_data.quantity
        else:
            # CartItem
            product_id = item_data.product_id
            size = item_data.size
            quantity = item_data.quantity

        # Use SELECT FOR UPDATE to lock row and prevent race conditions
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с ID {product_id} не найден"
            )

        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Товар {product.name} недоступен для заказа"
            )

        # Check availability
        if product.order_type == OrderType.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Товар {product.name} в режиме ожидания"
            )

        is_preorder = product.order_type == OrderType.PREORDER
        preorder_wave = None

        if is_preorder:
            # Check preorder availability
            if product.current_wave > product.preorder_waves_total:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Все волны предзаказа для {product.name} заполнены"
                )
            preorder_wave = product.current_wave
        else:
            # Check stock for specific size
            if size == "OKI" and product.oki_quantity < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Недостаточно товара {product.name} размера {size} на складе"
                )
            elif size == "BIG" and product.big_quantity < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Недостаточно товара {product.name} размера {size} на складе"
                )
            elif size not in ["OKI", "BIG"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Неверный размер {size}"
                )

        order_items_data.append({
            "product": product,
            "size": size,
            "quantity": quantity,
            "price": product.price,
            "is_preorder": is_preorder,
            "preorder_wave": preorder_wave
        })

    # Группировать items по типу (preorder или order)
    preorder_items = [item for item in order_items_data if item["is_preorder"]]
    order_items = [item for item in order_items_data if not item["is_preorder"]]

    created_orders = []

    # Функция для создания заказа
    def create_single_order(items, is_preorder_type):
        if not items:
            return None

        total_amount = sum(item["price"] * item["quantity"] for item in items)

        # Apply promo code only to order items, not preorder
        discount_amount = 0
        promo_code = None

        if not is_preorder_type and order_data.promo_code:
            promo_code = db.query(PromoCode).filter(
                PromoCode.code == order_data.promo_code
            ).first()

            if promo_code and promo_code.is_valid():
                if promo_code.discount_percent > 0:
                    discount_amount = total_amount * (promo_code.discount_percent / 100)
                elif promo_code.discount_amount > 0:
                    discount_amount = min(promo_code.discount_amount, total_amount)

        final_amount = total_amount - discount_amount

        # Generate order number
        order_number = f"DWC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        # Create order
        order = Order(
            user_id=current_user.id,
            order_number=order_number,
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            status=OrderStatus.created,  # Mark as created, payment will be handled separately
            delivery_address=order_data.delivery_address,
            cdek_point=order_data.cdek_point,
            postal_code=order_data.postal_code,
            promo_code_id=promo_code.id if promo_code else None
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        # Create order items
        for item_data in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product"].id,
                size=item_data["size"],
                quantity=item_data["quantity"],
                price=item_data["price"],
                is_preorder=item_data["is_preorder"],
                preorder_wave=item_data["preorder_wave"]
            )
            db.add(order_item)

            # Update stock or preorder count
            product = item_data["product"]
            if item_data["is_preorder"]:
                product.current_wave_count += item_data["quantity"]

                # Check if wave is full
                if product.current_wave_count >= product.preorder_wave_capacity:
                    product.current_wave += 1
                    product.current_wave_count = 0

                    # Check if all waves are done
                    if product.current_wave > product.preorder_waves_total:
                        product.order_type = OrderType.WAITING
            else:
                # Decrease stock for regular orders immediately
                size = item_data["size"]
                if size == "OKI":
                    product.oki_quantity -= item_data["quantity"]
                elif size == "BIG":
                    product.big_quantity -= item_data["quantity"]

        # Update promo code usage
        if promo_code:
            promo_code.current_uses += 1

        db.commit()
        db.refresh(order)
        return order

    # Создать заказ для обычных товаров
    if order_items:
        order = create_single_order(order_items, False)
        if order:
            created_orders.append(order)

    # Создать заказ для предзаказов
    if preorder_items:
        preorder_order = create_single_order(preorder_items, True)
        if preorder_order:
            created_orders.append(preorder_order)

    # Очистить корзину, если заказ создан из корзины
    if order_data.from_cart and cart:
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

    db.commit()

    return created_orders


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Частично обновить заказ (только для администраторов)
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Update fields
    update_data = order_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status":
            value = OrderStatus(value)
            if value == OrderStatus.shipped:
                order.shipped_at = datetime.utcnow()
        setattr(order, field, value)
    
    db.commit()
    db.refresh(order)
    
    return order


@router.get("/admin/all", response_model=OrderListResponse)
async def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Получить все заказы (только для администраторов)
    """
    from sqlalchemy.orm import joinedload

    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    # Use eager loading to include product data for admin
    orders = query.options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    return OrderListResponse(
        orders=orders,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )
