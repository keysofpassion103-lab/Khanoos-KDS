from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════
# MENU CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════

class MenuCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_order: int = 0


class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


# ═══════════════════════════════════════════════════════════════════════════
# MENU ITEMS
# ═══════════════════════════════════════════════════════════════════════════

class MenuItemCreate(BaseModel):
    category_id: Optional[str] = None
    item_name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    short_code: Optional[str] = None
    price: float = Field(ge=0)
    is_veg: bool = True
    image_url: Optional[str] = None


class MenuItemUpdate(BaseModel):
    category_id: Optional[str] = None
    item_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    short_code: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    is_veg: Optional[bool] = None
    is_available: Optional[bool] = None
    image_url: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# ORDERS
# ═══════════════════════════════════════════════════════════════════════════

class OrderItemInput(BaseModel):
    menu_item_id: str
    item_name: str
    quantity: int = Field(ge=1)
    price: float = Field(ge=0)
    is_veg: bool = True
    special_instructions: Optional[str] = None


class OrderCreate(BaseModel):
    order_type: str = Field(pattern="^(dine_in|takeaway|delivery)$")
    table_id: Optional[str] = None
    table_number: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = "cash"
    payment_status: Optional[str] = "pending"
    tax_percentage: float = 5.0
    discount_percentage: float = 0.0
    items: List[OrderItemInput]


class OrderAddItems(BaseModel):
    items: List[OrderItemInput]
    tax_percentage: float = 5.0


class OrderStatusUpdate(BaseModel):
    order_status: str = Field(pattern="^(new|preparing|ready|served|completed|cancelled)$")


class PaymentStatusUpdate(BaseModel):
    payment_status: str = Field(pattern="^(pending|paid|cancelled)$")
    payment_method: Optional[str] = None


class OrderPricingUpdate(BaseModel):
    subtotal: float = Field(ge=0)
    tax_percentage: float = Field(ge=0)
    discount_percentage: float = Field(ge=0, le=100)


# ═══════════════════════════════════════════════════════════════════════════
# KOTs
# ═══════════════════════════════════════════════════════════════════════════

class KOTItemInput(BaseModel):
    menu_item_id: Optional[str] = None
    item_name: str
    quantity: int = Field(ge=1)
    is_veg: bool = True
    special_instructions: Optional[str] = None


class KOTCreate(BaseModel):
    order_id: str
    items: List[KOTItemInput]


class KOTStatusUpdate(BaseModel):
    kot_status: str = Field(pattern="^(pending|preparing|ready|served)$")


# ═══════════════════════════════════════════════════════════════════════════
# SECTIONS
# ═══════════════════════════════════════════════════════════════════════════

class SectionCreate(BaseModel):
    section_name: str = Field(min_length=1, max_length=255)
    display_order: Optional[int] = None


class SectionUpdate(BaseModel):
    section_name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


# ═══════════════════════════════════════════════════════════════════════════
# TABLES
# ═══════════════════════════════════════════════════════════════════════════

class TableCreate(BaseModel):
    section_id: Optional[str] = None
    table_number: str = Field(min_length=1, max_length=50)
    capacity: int = Field(ge=1, default=4)
    is_ac: bool = False


class TableUpdate(BaseModel):
    section_id: Optional[str] = None
    table_number: Optional[str] = Field(None, min_length=1, max_length=50)
    capacity: Optional[int] = Field(None, ge=1)
    is_ac: Optional[bool] = None


class TableStatusUpdate(BaseModel):
    status: str = Field(pattern="^(available|occupied|reserved|cleaning)$")
