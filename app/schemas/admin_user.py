from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)

    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class AdminUserLogin(BaseModel):
    email: EmailStr
    password: str


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)


class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    created_at: datetime


class AdminLoginResponse(BaseModel):
    admin: AdminUserResponse
    access_token: str
    token_type: str = "bearer"


class AdminChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=100)

    @validator('new_password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v
