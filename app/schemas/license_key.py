from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class LicenseKeyCreate(BaseModel):
    license_key: str
    key_type: str = Field(..., description="license, master, or branch")
    outlet_id: Optional[str] = None
    chain_id: Optional[str] = None


class LicenseKeyResponse(BaseModel):
    id: str
    license_key: str
    key_type: str
    outlet_id: Optional[str] = None
    chain_id: Optional[str] = None
    is_used: bool = False
    used_at: Optional[datetime] = None
    used_by: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class LicenseVerifyRequest(BaseModel):
    license_key: str
    email: str


class LicenseAuthRequest(BaseModel):
    license_key: str
    email: str
    device_info: Optional[dict] = None


class LicenseVerifyResponse(BaseModel):
    valid: bool
    message: str
    outlet_id: Optional[str] = None
    outlet_name: Optional[str] = None
    owner_name: Optional[str] = None
    already_used: bool = False


class LicenseAuthResponse(BaseModel):
    success: bool
    message: str
    outlet_id: Optional[str] = None
    outlet_name: Optional[str] = None
    is_active: bool = False
    auth_user_id: Optional[str] = None


class OutletActivationRequest(BaseModel):
    outlet_id: str
    auth_user_id: str
    license_key: str


class OutletUserSignupRequest(BaseModel):
    """Outlet user signup with license key and password"""
    license_key: str
    email: str
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=2, max_length=255)


class OutletUserLoginRequest(BaseModel):
    """Outlet user login with email and password"""
    email: EmailStr
    password: str
