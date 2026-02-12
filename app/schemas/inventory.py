from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


# ═══════════════════════════════════════════════════════════════════════════
# INVENTORY CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════

class InventoryCategoryCreate(BaseModel):
    category_name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    display_order: int = 0


class InventoryCategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


# ═══════════════════════════════════════════════════════════════════════════
# VENDORS
# ═══════════════════════════════════════════════════════════════════════════

class VendorCreate(BaseModel):
    vendor_name: str = Field(min_length=1, max_length=255)
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


# ═══════════════════════════════════════════════════════════════════════════
# INVENTORY ITEMS
# ═══════════════════════════════════════════════════════════════════════════

class InventoryItemCreate(BaseModel):
    category_id: Optional[str] = None
    vendor_id: Optional[str] = None
    item_name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    unit: str = Field(min_length=1, max_length=50)
    current_stock: float = 0
    minimum_stock: float = 0
    maximum_stock: float = 0
    reorder_quantity: float = 0
    unit_cost: float = 0
    expiry_date: Optional[date] = None


class InventoryItemUpdate(BaseModel):
    category_id: Optional[str] = None
    vendor_id: Optional[str] = None
    item_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    current_stock: Optional[float] = None
    minimum_stock: Optional[float] = None
    maximum_stock: Optional[float] = None
    reorder_quantity: Optional[float] = None
    unit_cost: Optional[float] = None
    expiry_date: Optional[date] = None
    is_active: Optional[bool] = None


class StockUpdate(BaseModel):
    current_stock: float = Field(ge=0)


# ═══════════════════════════════════════════════════════════════════════════
# RECIPE ITEMS
# ═══════════════════════════════════════════════════════════════════════════

class RecipeItemCreate(BaseModel):
    menu_item_id: str
    inventory_item_id: str
    quantity_required: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=50)
    notes: Optional[str] = None


class RecipeItemUpdate(BaseModel):
    quantity_required: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# INVENTORY TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════

class TransactionCreate(BaseModel):
    inventory_item_id: str
    transaction_type: str = Field(pattern="^(purchase|usage|adjustment|waste)$")
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=50)
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# INVENTORY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

class CanPrepareRequest(BaseModel):
    menu_item_id: str
    quantity: int = Field(ge=1, default=1)


class ValidateOrderInventoryRequest(BaseModel):
    order_items: List[dict]
