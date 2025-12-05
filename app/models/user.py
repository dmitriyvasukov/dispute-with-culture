from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class User(Base):
    """User model - клиенты и администраторы"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Profile info
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Delivery info
    address = Column(Text, nullable=True)
    cdek_point = Column(String(255), nullable=True)
    
    # Social
    telegram = Column(String(255), nullable=True)
    vk = Column(String(255), nullable=True)
    
    # Status
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    cart = relationship("Cart", back_populates="user", cascade="all, delete-orphan", uselist=False)

    def __repr__(self):
        return f"<User {self.phone}>"
