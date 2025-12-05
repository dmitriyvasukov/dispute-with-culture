from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid
from datetime import datetime
import shutil

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.product import Product, ProductMedia, OrderType, ProductionStatus
from app.models.order import OrderItem
from app.models.cart import CartItem
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse

router = APIRouter()


@router.post("/upload-images", response_model=List[str])
async def upload_product_images(
    files: List[UploadFile] = File(...),
    current_admin = Depends(get_current_admin)
):
    """
    Загрузка изображений для товаров (только для администраторов)
    """
    uploaded_urls = []

    # Создаем директорию для загрузок, если она не существует
    upload_dir = "static/uploads/products"
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        # Проверяем тип файла
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Файл {file.filename} не является изображением"
            )

        # Генерируем уникальное имя файла
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Формируем URL для доступа к файлу
        file_url = f"/static/uploads/products/{unique_filename}"
        uploaded_urls.append(file_url)

    return uploaded_urls


@router.post("/upload-preview-image", response_model=str)
async def upload_preview_image(
    file: UploadFile = File(...),
    current_admin = Depends(get_current_admin)
):
    """
    Загрузка превью изображения для товара (только для администраторов)
    """
    # Проверяем тип файла
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл {file.filename} не является изображением"
        )

    # Создаем директорию для загрузок, если она не существует
    upload_dir = "static/uploads/products"
    os.makedirs(upload_dir, exist_ok=True)

    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"preview_{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Формируем URL для доступа к файлу
    file_url = f"/static/uploads/products/{unique_filename}"
    return file_url


@router.get("/", response_model=ProductListResponse)
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_active: Optional[bool] = None,
    is_archived: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    """
    Получить список товаров
    """
    query = db.query(Product)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    if is_archived is not None:
        query = query.filter(Product.is_archived == is_archived)
    
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    
    return ProductListResponse(
        products=products,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Получить товар по ID
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Создать новый товар (только для администраторов)
    """
    # Check if article already exists
    existing = db.query(Product).filter(Product.article == product_data.article).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Товар с таким артикулом уже существует"
        )
    
    # Create product
    product = Product(
        name=product_data.name,
        description=product_data.description,
        article=product_data.article,
        price=product_data.price,
        oki_quantity=product_data.oki_quantity,
        big_quantity=product_data.big_quantity,
        size_table=product_data.size_table,
        care_instructions=product_data.care_instructions,
        preview_image_url=product_data.preview_image_url,
        order_type=OrderType(product_data.order_type),
        preorder_waves_total=product_data.preorder_waves_total,
        preorder_wave_capacity=product_data.preorder_wave_capacity
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Add media
    for idx, url in enumerate(product_data.media_urls):
        media = ProductMedia(product_id=product.id, url=url, order=idx)
        db.add(media)
    
    db.commit()
    db.refresh(product)
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Обновить товар (только для администраторов)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    # Update fields
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "order_type" and value:
            value = OrderType(value)
        elif field == "production_status" and value:
            value = ProductionStatus(value)
        elif field == "media_urls":
            # Handle media updates
            if value is not None:
                # Get existing media before deleting
                existing_media = db.query(ProductMedia).filter(ProductMedia.product_id == product_id).all()

                # Delete existing media records
                db.query(ProductMedia).filter(ProductMedia.product_id == product_id).delete()

                # Remove old files from filesystem
                for media in existing_media:
                    file_path = os.path.join("static", media.url.lstrip("/"))
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass  # Ignore if file doesn't exist or can't be removed

                # Add new media
                for idx, url in enumerate(value):
                    media = ProductMedia(product_id=product_id, url=url, order=idx)
                    db.add(media)
            continue
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Удалить товар (только для администраторов)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    # Check if product has related order items or cart items
    has_order_items = db.query(OrderItem).filter(OrderItem.product_id == product_id).first() is not None
    has_cart_items = db.query(CartItem).filter(CartItem.product_id == product_id).first() is not None

    if has_order_items or has_cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить товар, который используется в заказах или корзинах"
        )

    # Get existing media before deleting product
    existing_media = db.query(ProductMedia).filter(ProductMedia.product_id == product_id).all()

    # Remove media files from filesystem
    for media in existing_media:
        file_path = os.path.join("static", media.url.lstrip("/"))
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass  # Ignore if file doesn't exist or can't be removed

    # Also remove preview image if exists
    if product.preview_image_url:
        preview_path = os.path.join("static", product.preview_image_url.lstrip("/"))
        if os.path.exists(preview_path):
            try:
                os.remove(preview_path)
            except OSError:
                pass  # Ignore if file doesn't exist or can't be removed

    db.delete(product)
    db.commit()

    return None


@router.post("/{product_id}/archive", response_model=ProductResponse)
async def archive_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Архивировать товар (только для администраторов)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )
    
    product.is_archived = True
    product.is_active = False
    
    db.commit()
    db.refresh(product)
    
    return product
