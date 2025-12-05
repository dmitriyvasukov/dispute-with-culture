from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.order import Order, OrderItem, PaymentStatus
from app.services.payment import payment_service

router = APIRouter()


@router.post("/create/{order_id}")
async def create_payment(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Создать платеж для заказа через ЮKassa
    """
    # Получить заказ
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )

    # Проверить, что заказ принадлежит пользователю
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    # Проверить, что заказ не оплачен
    if order.payment_status == PaymentStatus.SUCCEEDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заказ уже оплачен"
        )

    # Загрузить связанные данные для платежа
    from sqlalchemy.orm import joinedload
    order = db.query(Order).options(
        joinedload(Order.user),
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(Order.id == order_id).first()

    try:
        # Создать платеж через сервис
        payment_result = payment_service.create_payment(order)

        # Обновить заказ с данными платежа
        order.payment_id = payment_result["payment_id"]
        order.payment_url = payment_result["confirmation_url"]
        order.payment_status = PaymentStatus.PENDING

        db.commit()

        return {
            "payment_id": payment_result["payment_id"],
            "confirmation_url": payment_result["confirmation_url"],
            "status": payment_result["status"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания платежа: {str(e)}"
        )


@router.get("/callback")
async def payment_callback(
    orderId: str = None,
    paymentId: str = None,
    status: str = None
):
    """
    Callback от ЮKassa после оплаты
    """
    # Здесь можно обработать callback, но для простоты возвращаем успех
    return {"status": "success"}


@router.post("/webhook")
async def payment_webhook(
    request_body: dict,
    db: Session = Depends(get_db)
):
    """
    Webhook от ЮKassa для уведомлений о статусе платежа
    """
    try:
        # Обработать webhook через сервис
        webhook_data = payment_service.process_webhook(request_body)

        # Найти заказ по payment_id из метаданных
        payment_id = webhook_data.get("payment_id")
        if payment_id:
            order = db.query(Order).filter(Order.payment_id == payment_id).first()
            if order:
                if webhook_data["event"] == "payment.succeeded":
                    order.payment_status = PaymentStatus.SUCCEEDED
                    order.status = "paid"  # Обновить статус заказа
                    order.paid_at = datetime.utcnow()
                elif webhook_data["event"] == "payment.canceled":
                    order.payment_status = PaymentStatus.CANCELLED

                db.commit()

        return {"status": "processed"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки webhook: {str(e)}"
        )