from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import random

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.splash import SplashNotification
from app.schemas.splash import (
    SplashNotificationCreate,
    SplashNotificationUpdate,
    SplashNotificationResponse,
    SplashNotificationListResponse,
    RandomSplashResponse
)

router = APIRouter()


@router.get("/random", response_model=RandomSplashResponse)
async def get_random_splash(db: Session = Depends(get_db)):
    """
    Получить случайное активное splash уведомление
    """
    active_notifications = db.query(SplashNotification).filter(
        SplashNotification.is_active == True
    ).all()

    if not active_notifications:
        # Return default message if no active notifications
        return RandomSplashResponse(text="Добро пожаловать в DWC Shop!")

    random_notification = random.choice(active_notifications)
    return RandomSplashResponse(text=random_notification.text)


@router.get("/", response_model=SplashNotificationListResponse)
async def get_splash_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Получить список splash уведомлений (только для администраторов)
    """
    query = db.query(SplashNotification)

    if is_active is not None:
        query = query.filter(SplashNotification.is_active == is_active)

    total = query.count()
    notifications = query.offset(skip).limit(limit).all()

    return SplashNotificationListResponse(
        notifications=notifications,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/{notification_id}", response_model=SplashNotificationResponse)
async def get_splash_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Получить splash уведомление по ID (только для администраторов)
    """
    notification = db.query(SplashNotification).filter(
        SplashNotification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено"
        )

    return notification


@router.post("/", response_model=SplashNotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_splash_notification(
    notification_data: SplashNotificationCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Создать новое splash уведомление (только для администраторов)
    """
    notification = SplashNotification(
        text=notification_data.text,
        is_active=notification_data.is_active
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


@router.put("/{notification_id}", response_model=SplashNotificationResponse)
async def update_splash_notification(
    notification_id: int,
    notification_data: SplashNotificationUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Обновить splash уведомление (только для администраторов)
    """
    notification = db.query(SplashNotification).filter(
        SplashNotification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено"
        )

    update_data = notification_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notification, field, value)

    db.commit()
    db.refresh(notification)

    return notification


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_splash_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Удалить splash уведомление (только для администраторов)
    """
    notification = db.query(SplashNotification).filter(
        SplashNotification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено"
        )

    db.delete(notification)
    db.commit()