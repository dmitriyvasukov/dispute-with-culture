from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from app.core.database import Base


class SplashNotification(Base):
    """Splash notification model - уведомления при запуске"""
    __tablename__ = "splash_notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Notification text
    text = Column(String(120), nullable=False)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SplashNotification {self.id}: {self.text[:20]}...>"