from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class PreorderStatusType(str, enum.Enum):
    """Статусы предзаказов"""
    COLLECTING = "Набор предзаказов"
    PRODUCTION = "Производство изделий"
    TRACKING = "Формирование трек-номера"
    SHIPPING = "Отправка изделий"


class PreorderWave(Base):
    """Preorder wave - волны предзаказов"""
    __tablename__ = "preorder_waves"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Wave info
    wave_number = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    current_count = Column(Integer, default=0)
    
    # Status
    status = Column(Enum(PreorderStatusType), default=PreorderStatusType.COLLECTING, nullable=False)
    is_completed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<PreorderWave {self.wave_number} for Product {self.product_id}>"


class PreorderStatus(Base):
    """Preorder status - статусы конкретных предзаказов в заказах"""
    __tablename__ = "preorder_statuses"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    wave_id = Column(Integer, ForeignKey("preorder_waves.id"), nullable=False)
    
    # Status
    status = Column(Enum(PreorderStatusType), default=PreorderStatusType.COLLECTING, nullable=False)
    status_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PreorderStatus for Order {self.order_id}>"
