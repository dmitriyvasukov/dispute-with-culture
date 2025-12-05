"""
Payment service for YooKassa integration
"""
from typing import Optional
from yookassa import Configuration, Payment as YKPayment
from yookassa.domain.models import Currency
from yookassa.domain.request import PaymentRequestBuilder
from yookassa.domain.notification import WebhookNotificationFactory, WebhookNotificationEventType

from app.core.config import settings
from app.models.order import Order


class PaymentService:
    """Service for handling payments via YooKassa"""
    
    def __init__(self):
        """Initialize YooKassa configuration"""
        Configuration.account_id = settings.YUKASSA_SHOP_ID
        Configuration.secret_key = settings.YUKASSA_SECRET_KEY
    
    def create_payment(self, order: Order) -> dict:
        """
        Create payment for order
        
        Args:
            order: Order object (must have user and items loaded)
            
        Returns:
            dict with payment_id and confirmation_url
        """
        # Validate that relationships are loaded to avoid lazy loading errors
        if not order.user:
            raise Exception("Order must have user relationship loaded")
        
        if not order.items:
            raise Exception("Order must have items relationship loaded")
        
        payment_builder = PaymentRequestBuilder()
        
        payment_builder.set_amount({
            "value": str(order.final_amount),
            "currency": Currency.RUB
        })
        
        payment_builder.set_confirmation({
            "type": "redirect",
            "return_url": settings.YUKASSA_RETURN_URL
        })
        
        payment_builder.set_capture(True)
        
        payment_builder.set_description(f"Заказ {order.order_number}")
        
        payment_builder.set_metadata({
            "order_id": order.id,
            "order_number": order.order_number
        })
        
        # Add receipt for 54-FZ law compliance
        payment_builder.set_receipt({
            "customer": {
                "phone": order.user.phone,
                "email": order.user.email or "noreply@dwc-shop.com"
            },
            "items": [
                {
                    "description": f"{item.product.name if item.product else 'Unknown Product'} ({item.size})",
                    "quantity": str(item.quantity),
                    "amount": {
                        "value": str(item.price),
                        "currency": Currency.RUB
                    },
                    "vat_code": 1  # Without VAT
                }
                for item in order.items
            ]
        })
        
        payment_request = payment_builder.build()
        
        try:
            payment = YKPayment.create(payment_request)
            
            return {
                "payment_id": payment.id,
                "confirmation_url": payment.confirmation.confirmation_url,
                "status": payment.status
            }
        except Exception as e:
            raise Exception(f"Ошибка создания платежа: {str(e)}")
    
    def get_payment(self, payment_id: str) -> Optional[dict]:
        """
        Get payment information
        
        Args:
            payment_id: Payment ID from YooKassa
            
        Returns:
            dict with payment info or None
        """
        try:
            payment = YKPayment.find_one(payment_id)
            
            return {
                "id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "amount": float(payment.amount.value),
                "created_at": payment.created_at,
                "captured_at": payment.captured_at,
                "metadata": payment.metadata
            }
        except Exception as e:
            print(f"Ошибка получения платежа: {str(e)}")
            return None
    
    def cancel_payment(self, payment_id: str) -> bool:
        """
        Cancel payment
        
        Args:
            payment_id: Payment ID from YooKassa
            
        Returns:
            True if cancelled successfully
        """
        try:
            payment = YKPayment.cancel(payment_id)
            return payment.status == "cancelled"
        except Exception as e:
            print(f"Ошибка отмены платежа: {str(e)}")
            return False
    
    def process_webhook(self, request_body: dict) -> dict:
        """
        Process webhook notification from YooKassa
        
        Args:
            request_body: Webhook notification body
            
        Returns:
            dict with event info
        """
        try:
            notification = WebhookNotificationFactory().create(request_body)
            
            payment = notification.object
            
            return {
                "event": notification.event,
                "payment_id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "metadata": payment.metadata
            }
        except Exception as e:
            raise Exception(f"Ошибка обработки webhook: {str(e)}")


# Singleton instance
payment_service = PaymentService()
