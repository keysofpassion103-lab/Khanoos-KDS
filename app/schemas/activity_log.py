from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ActivityLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    outlet_id: Optional[str] = None
    chain_id: Optional[str] = None
    action: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime


class ActivityLogFilter(BaseModel):
    outlet_id: Optional[str] = None
    chain_id: Optional[str] = None
    action: Optional[str] = None
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
