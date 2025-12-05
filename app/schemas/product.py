from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProductMediaBase(BaseModel):
    url: str
    order: int = 0


class ProductMediaResponse(ProductMediaBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., description="Название товара")
    description: Optional[str] = Field(None, description="Описание")
    article: str = Field(..., description="Артикул")
    price: float = Field(..., gt=0, description="Цена")
    oki_quantity: int = Field(default=0, description="Количество размера OKI")
    big_quantity: int = Field(default=0, description="Количество размера BIG")
    size_table: Optional[Dict[str, Any]] = Field(None, description="Таблица размеров (свойства размеров)")
    care_instructions: Optional[str] = Field(None, description="Инструкции по уходу")
    preview_image_url: Optional[str] = Field(None, description="URL превью изображения для карточки товара")


class ProductCreate(ProductBase):
    order_type: str = Field(default="order", description="Тип заказа: order, preorder, waiting")
    preorder_waves_total: int = Field(default=0, description="Количество волн предзаказа")
    preorder_wave_capacity: int = Field(default=0, description="Вместимость волны")
    media_urls: List[str] = Field(default_factory=list, description="URL фотографий галереи")


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    oki_quantity: Optional[int] = None
    big_quantity: Optional[int] = None
    size_table: Optional[Dict[str, Any]] = None
    care_instructions: Optional[str] = None
    preview_image_url: Optional[str] = None
    order_type: Optional[str] = None
    preorder_waves_total: Optional[int] = None
    preorder_wave_capacity: Optional[int] = None
    production_status: Optional[str] = None
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None
    media_urls: Optional[List[str]] = None


class ProductResponse(ProductBase):
    id: int
    order_type: str
    stock_count: int
    preorder_waves_total: int
    preorder_wave_capacity: int
    current_wave: int
    current_wave_count: int
    production_status: Optional[str] = None  # Статус производства для предзаказов
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    media: List[ProductMediaResponse] = []
    sizes: Dict[str, int]  # Для совместимости с фронтендом

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
