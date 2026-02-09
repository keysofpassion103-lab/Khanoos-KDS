from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class SubscriptionResponse(BaseModel):
    id: str
    outlet_id: Optional[str] = None
    chain_id: Optional[str] = None
    plan_id: str
    start_date: datetime
    end_date: datetime
    amount_paid: Optional[Decimal] = None
    payment_status: str = "pending"
    is_active: bool = True
    auto_renew: bool = False
    created_at: datetime


class RenewalRequest(BaseModel):
    plan_id: str
    amount_paid: Decimal = Field(ge=0)


class RenewalResponse(BaseModel):
    success: bool
    message: str
    new_end_date: Optional[datetime] = None
