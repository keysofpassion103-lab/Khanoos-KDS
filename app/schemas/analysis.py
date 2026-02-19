from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class DailyAnalysisResponse(BaseModel):
    """Response model for daily analysis data"""
    id: Optional[str] = None
    outlet_id: str
    analysis_date: str
    dine_in_count: int = 0
    takeaway_count: int = 0
    delivery_count: int = 0
    total_orders: int = 0
    dine_in_revenue: float = 0.0
    takeaway_revenue: float = 0.0
    delivery_revenue: float = 0.0
    total_revenue: float = 0.0
    cash_revenue: float = 0.0
    card_revenue: float = 0.0
    upi_revenue: float = 0.0
    razorpay_revenue: float = 0.0
    other_revenue: float = 0.0
    cash_count: int = 0
    card_count: int = 0
    upi_count: int = 0
    razorpay_count: int = 0
    other_count: int = 0
    cancelled_orders: int = 0
    average_order_value: float = 0.0
    tax_collected: float = 0.0
    discount_given: float = 0.0


class CurrencyDenominationCreate(BaseModel):
    """Request model for saving currency denomination"""
    record_date: str
    notes_500: int = Field(default=0, ge=0)
    notes_200: int = Field(default=0, ge=0)
    notes_100: int = Field(default=0, ge=0)
    notes_50: int = Field(default=0, ge=0)
    notes_20: int = Field(default=0, ge=0)
    notes_10: int = Field(default=0, ge=0)
    coins_20: int = Field(default=0, ge=0)
    coins_10: int = Field(default=0, ge=0)
    coins_5: int = Field(default=0, ge=0)
    coins_2: int = Field(default=0, ge=0)
    coins_1: int = Field(default=0, ge=0)