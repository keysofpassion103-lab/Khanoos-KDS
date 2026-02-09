from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChainOutletCreate(BaseModel):
    chain_name: str = Field(min_length=2, max_length=255)
    master_admin_name: str = Field(min_length=2, max_length=255)
    master_admin_email: str
    master_admin_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    business_address: Optional[str] = None
    business_city: Optional[str] = None
    business_state: Optional[str] = None
    business_pincode: Optional[str] = None
    total_outlets: int = Field(default=0, ge=0)
    plan_id: str


class ChainOutletUpdate(BaseModel):
    chain_name: Optional[str] = Field(None, min_length=2, max_length=255)
    master_admin_name: Optional[str] = Field(None, min_length=2, max_length=255)
    master_admin_email: Optional[str] = None
    master_admin_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    business_address: Optional[str] = None
    business_city: Optional[str] = None
    business_state: Optional[str] = None
    business_pincode: Optional[str] = None
    total_outlets: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ChainOutletResponse(BaseModel):
    id: str
    chain_name: str
    master_admin_name: str
    master_admin_email: str
    master_admin_phone: Optional[str] = None
    business_address: Optional[str] = None
    business_city: Optional[str] = None
    business_state: Optional[str] = None
    business_pincode: Optional[str] = None
    master_license_key: str
    master_key_used: bool = False
    total_outlets: int = 0
    plan_id: Optional[str] = None
    plan_start_date: Optional[datetime] = None
    plan_end_date: Optional[datetime] = None
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
