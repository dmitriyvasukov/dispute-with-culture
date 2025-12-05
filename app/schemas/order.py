from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

from app.schemas.product import ProductResponse


class OrderItemBase(BaseModel):
    product_id: int
    size: str
    quantity: int = Field(default=1, ge=1)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    price: float
    is_preorder: bool
    preorder_wave: Optional[int] = None
    created_at: datetime
    product: Optional[ProductResponse] = None  # Product data

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    delivery_address: Optional[str] = None
    cdek_point: Optional[str] = None
    postal_code: Optional[str] = None
    promo_code: Optional[str] = None


class OrderCreate(OrderBase):
    items: Optional[List[OrderItemCreate]] = None
    from_cart: bool = False


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    tracking_number: Optional[str] = None
    delivery_address: Optional[str] = None
    cdek_point: Optional[str] = None
    postal_code: Optional[str] = None


class BulkPreorderStatusUpdate(BaseModel):
    order_ids: List[int]
    status: str


class OrderResponse(BaseModel):
    id: int
    order_number: str
    total_amount: float
    discount_amount: float
    final_amount: float
    status: str
    tracking_number: Optional[str] = None
    delivery_address: Optional[str] = None
    cdek_point: Optional[str] = None
    postal_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    shipped_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int
