from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SingleOutletCreate(BaseModel):
    outlet_name: str = Field(min_length=2, max_length=255)
    outlet_type: str = "single"
    owner_name: str = Field(min_length=2, max_length=255)
    owner_email: str
    owner_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    plan_id: str
    chain_id: Optional[str] = None


class SingleOutletUpdate(BaseModel):
    outlet_name: Optional[str] = Field(None, min_length=2, max_length=255)
    outlet_type: Optional[str] = None
    owner_name: Optional[str] = Field(None, min_length=2, max_length=255)
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    is_active: Optional[bool] = None


class SingleOutletResponse(BaseModel):
    id: str
    outlet_name: str
    outlet_type: str = "single"
    owner_name: str
    owner_email: str
    owner_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    license_key: str
    license_key_used: bool = False
    plan_id: Optional[str] = None
    plan_start_date: Optional[datetime] = None
    plan_end_date: Optional[datetime] = None
    is_active: bool
    chain_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime


class OutletStatusResponse(BaseModel):
    is_active: bool
    plan_expired: bool
    days_remaining: int
    plan_end_date: Optional[datetime] = None
