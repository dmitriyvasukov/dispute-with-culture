from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SplashNotificationBase(BaseModel):
    text: str = Field(..., max_length=120, description="Текст уведомления")
    is_active: bool = Field(default=True, description="Активно ли уведомление")


class SplashNotificationCreate(SplashNotificationBase):
    pass


class SplashNotificationUpdate(BaseModel):
    text: Optional[str] = Field(None, max_length=120)
    is_active: Optional[bool] = None


class SplashNotificationResponse(SplashNotificationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SplashNotificationListResponse(BaseModel):
    notifications: list[SplashNotificationResponse]
    total: int
    page: int
    page_size: int


class RandomSplashResponse(BaseModel):
    text: str