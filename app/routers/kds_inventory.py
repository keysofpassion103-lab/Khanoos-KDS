from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from app.schemas.inventory import (
    InventoryCategoryCreate, InventoryCategoryUpdate,
    VendorCreate, VendorUpdate,
    InventoryItemCreate, InventoryItemUpdate, StockUpdate,
    RecipeItemCreate, RecipeItemUpdate,
    TransactionCreate,
    CanPrepareRequest, ValidateOrderInventoryRequest,
)
from app.schemas.response import APIResponse
from app.services.inventory_service import InventoryService
from app.auth.dependencies import get_current_outlet_user

router = APIRouter(prefix="/kds/inventory", tags=["KDS Inventory"])


# ═══════════════════════════════════════════════════════════════════════════
# INVENTORY CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/categories", response_model=APIResponse)
async def get_categories(current_user: dict = Depends(get_current_outlet_user)):
    result = await InventoryService.get_categories(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/categories", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: InventoryCategoryCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.create_category(current_user["outlet_id"], data)
    return APIResponse(success=True, message="Category created successfully", data=result)


@router.put("/categories/{category_id}", response_model=APIResponse)
async def update_category(
    category_id: str,
    data: InventoryCategoryUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.update_category(category_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Category updated successfully", data=result)


@router.delete("/categories/{category_id}", response_model=APIResponse)
async def delete_category(
    category_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    await InventoryService.delete_category(category_id, current_user["outlet_id"])
    return APIResponse(success=True, message="Category deleted successfully")


# ═══════════════════════════════════════════════════════════════════════════
# VENDORS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/vendors", response_model=APIResponse)
async def get_vendors(current_user: dict = Depends(get_current_outlet_user)):
    result = await InventoryService.get_vendors(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/vendors", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.create_vendor(current_user["outlet_id"], data)
    return APIResponse(success=True, message="Vendor created successfully", data=result)


@router.put("/vendors/{vendor_id}", response_model=APIResponse)
async def update_vendor(
    vendor_id: str,
    data: VendorUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.update_vendor(vendor_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Vendor updated successfully", data=result)


@router.delete("/vendors/{vendor_id}", response_model=APIResponse)
async def delete_vendor(
    vendor_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    await InventoryService.delete_vendor(vendor_id, current_user["outlet_id"])
    return APIResponse(success=True, message="Vendor deleted successfully")


# ═══════════════════════════════════════════════════════════════════════════
# INVENTORY ITEMS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/items", response_model=APIResponse)
async def get_items(current_user: dict = Depends(get_current_outlet_user)):
    result = await InventoryService.get_items(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.get("/items/{item_id}", response_model=APIResponse)
async def get_item(
    item_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.get_item(item_id, current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/items", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    data: InventoryItemCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.create_item(current_user["outlet_id"], data)
    return APIResponse(success=True, message="Item created successfully", data=result)


@router.put("/items/{item_id}", response_model=APIResponse)
async def update_item(
    item_id: str,
    data: InventoryItemUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.update_item(item_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Item updated successfully", data=result)


@router.patch("/items/{item_id}/stock", response_model=APIResponse)
async def update_stock(
    item_id: str,
    data: StockUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.update_stock(item_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Stock updated successfully", data=result)


@router.delete("/items/{item_id}", response_model=APIResponse)
async def delete_item(
    item_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    await InventoryService.delete_item(item_id, current_user["outlet_id"])
    return APIResponse(success=True, message="Item deleted successfully")


# ═══════════════════════════════════════════════════════════════════════════
# RECIPE ITEMS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/recipes/{menu_item_id}", response_model=APIResponse)
async def get_recipe_items(
    menu_item_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.get_recipe_items(menu_item_id, current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/recipes", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe_item(
    data: RecipeItemCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.create_recipe_item(data, current_user["outlet_id"])
    return APIResponse(success=True, message="Recipe item created successfully", data=result)


@router.put("/recipes/{recipe_item_id}", response_model=APIResponse)
async def update_recipe_item(
    recipe_item_id: str,
    data: RecipeItemUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.update_recipe_item(recipe_item_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Recipe item updated successfully", data=result)


@router.delete("/recipes/{recipe_item_id}", response_model=APIResponse)
async def delete_recipe_item(
    recipe_item_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    await InventoryService.delete_recipe_item(recipe_item_id, current_user["outlet_id"])
    return APIResponse(success=True, message="Recipe item deleted successfully")


# ═══════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/transactions", response_model=APIResponse)
async def get_transactions(
    inventory_item_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.get_transactions(
        current_user["outlet_id"],
        inventory_item_id=inventory_item_id,
        limit=limit
    )
    return APIResponse(success=True, data=result)


@router.post("/transactions", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.create_transaction(
        current_user["outlet_id"],
        data,
        user_id=current_user.get("user_id")
    )
    return APIResponse(success=True, message="Transaction recorded successfully", data=result)


# ═══════════════════════════════════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/alerts", response_model=APIResponse)
async def get_alerts(
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.get_alerts(
        current_user["outlet_id"],
        unread_only=unread_only
    )
    return APIResponse(success=True, data=result)


@router.patch("/alerts/{alert_id}/read", response_model=APIResponse)
async def mark_alert_read(
    alert_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    result = await InventoryService.mark_alert_read(alert_id, current_user["outlet_id"])
    return APIResponse(success=True, message="Alert marked as read", data=result)


@router.post("/alerts/read-all", response_model=APIResponse)
async def mark_all_alerts_read(current_user: dict = Depends(get_current_outlet_user)):
    result = await InventoryService.mark_all_alerts_read(current_user["outlet_id"])
    return APIResponse(success=True, message="All alerts marked as read", data=result)


# ═══════════════════════════════════════════════════════════════════════════
# RPC FUNCTION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/summary", response_model=APIResponse)
async def get_inventory_summary(current_user: dict = Depends(get_current_outlet_user)):
    """Get inventory summary (total, low stock, expired, etc.)"""
    result = await InventoryService.get_inventory_summary(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.get("/recipe-cost/{menu_item_id}", response_model=APIResponse)
async def get_recipe_cost(
    menu_item_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Get recipe cost for a menu item"""
    result = await InventoryService.get_recipe_cost(menu_item_id, current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/can-prepare", response_model=APIResponse)
async def can_prepare_item(
    data: CanPrepareRequest,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Check if a menu item can be prepared with current inventory"""
    result = await InventoryService.can_prepare_item(
        data.menu_item_id, data.quantity, outlet_id=current_user["outlet_id"]
    )
    return APIResponse(success=True, data=result)


@router.get("/recipe-conversion/{menu_item_id}", response_model=APIResponse)
async def get_recipe_with_conversion(
    menu_item_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Get recipe details with unit conversion"""
    result = await InventoryService.get_recipe_with_conversion(menu_item_id, current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.get("/low-stock", response_model=APIResponse)
async def get_low_stock_items(current_user: dict = Depends(get_current_outlet_user)):
    """Get items that are low on stock or out of stock"""
    result = await InventoryService.get_low_stock_items(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/deduct-order/{order_id}", response_model=APIResponse)
async def deduct_inventory_for_order(
    order_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Deduct inventory for an entire order"""
    result = await InventoryService.deduct_inventory_for_order(order_id, current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/validate-order", response_model=APIResponse)
async def validate_order_inventory(
    data: ValidateOrderInventoryRequest,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Validate if inventory is sufficient for order items"""
    result = await InventoryService.validate_order_inventory(data.order_items)
    return APIResponse(success=True, data=result)
