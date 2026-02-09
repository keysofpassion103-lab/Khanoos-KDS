from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PlanTypeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    duration_days: int = Field(gt=0)
    price: Decimal = Field(ge=0)
    features: Optional[dict] = None


class PlanTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    duration_days: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, ge=0)
    features: Optional[dict] = None
    is_active: Optional[bool] = None


class PlanTypeResponse(BaseModel):
    id: str
    name: str
    duration_days: int
    price: Decimal
    features: Optional[dict] = None
    is_active: bool
    created_at: datetime
