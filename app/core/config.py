from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "DWC Shop"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://dwc_user:dwc_password@localhost:5432/dwc_shop"
    POSTGRES_USER: str = "dwc_user"
    POSTGRES_PASSWORD: str = "dwc_password"
    POSTGRES_DB: str = "dwc_shop"
    
    # Security
    SECRET_KEY: str = "dwc-secret-key-change-this-in-production-12345678"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # Admin
    ADMIN_PHONE: str = "+79999999999"
    ADMIN_PASSWORD: str = "admin123"
    
    # ЮKassa
    YUKASSA_SHOP_ID: str = "1220486"
    YUKASSA_SECRET_KEY: str = "test_XbJJR3kHH8y0zLjyuZ7JS7s9_KYL_MRsvkuhiJc6CEs"
    YUKASSA_RETURN_URL: str = "http://localhost:8000/api/v1/payment/callback"
    
    # SMS
    SMS_PROVIDER: str = "test"
    SMS_API_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "https://dispute-with-culture.com"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from environment


settings = Settings()
