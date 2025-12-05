from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import phonenumbers


class UserBase(BaseModel):
    phone: str = Field(..., description="Номер телефона")
    
    @validator('phone')
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, "RU")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError('Неверный формат номера телефона')
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValueError('Неверный формат номера телефона')


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Пароль")


class UserLogin(BaseModel):
    phone: str
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    cdek_point: Optional[str] = None
    telegram: Optional[str] = None
    vk: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=6, description="Новый пароль")


class UserResponse(BaseModel):
    id: int
    phone: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    cdek_point: Optional[str] = None
    telegram: Optional[str] = None
    vk: Optional[str] = None
    is_admin: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
