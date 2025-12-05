from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CartItemBase(BaseModel):
    product_id: int
    size: str
    quantity: int = Field(default=1, ge=1)


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(CartItemBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    items: List[CartItemResponse] = []

    class Config:
        from_attributes = True


class CartItemWithProductResponse(CartItemResponse):
    product_name: str
    product_price: float
    product_article: str

    class Config:
        from_attributes = True


class CartWithProductsResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    items: List[CartItemWithProductResponse] = []
    total_items: int = 0
    total_amount: float = 0.0

    class Config:
        from_attributes = True