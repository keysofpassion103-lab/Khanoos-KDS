from fastapi import APIRouter, Depends, status
from app.schemas.kds import MenuCategoryCreate, MenuCategoryUpdate, MenuItemCreate, MenuItemUpdate
from app.schemas.response import APIResponse
from app.services.kds_menu_service import KDSMenuService
from app.auth.dependencies import get_current_outlet_user

router = APIRouter(prefix="/kds/menu", tags=["KDS Menu"])


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORIES (Global - no outlet_id in SQL table)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/categories", response_model=APIResponse)
async def get_categories(current_user: dict = Depends(get_current_outlet_user)):
    """Get all active menu categories"""
    result = await KDSMenuService.get_categories()
    return APIResponse(success=True, data=result)


@router.post("/categories", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: MenuCategoryCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Create a new menu category"""
    result = await KDSMenuService.create_category(data)
    return APIResponse(success=True, message="Category created successfully", data=result)


@router.put("/categories/{category_id}", response_model=APIResponse)
async def update_category(
    category_id: str,
    data: MenuCategoryUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Update a menu category"""
    result = await KDSMenuService.update_category(category_id, data)
    return APIResponse(success=True, message="Category updated successfully", data=result)


@router.delete("/categories/{category_id}", response_model=APIResponse)
async def delete_category(
    category_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Delete a menu category"""
    await KDSMenuService.delete_category(category_id)
    return APIResponse(success=True, message="Category deleted successfully")


# ═══════════════════════════════════════════════════════════════════════════
# MENU ITEMS (Scoped to outlet)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/items", response_model=APIResponse)
async def get_menu_items(current_user: dict = Depends(get_current_outlet_user)):
    """Get all menu items for the current outlet"""
    result = await KDSMenuService.get_menu_items(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.get("/items/{item_id}", response_model=APIResponse)
async def get_menu_item(
    item_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Get a single menu item"""
    result = await KDSMenuService.get_menu_item(item_id, current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/items", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    data: MenuItemCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Create a new menu item"""
    result = await KDSMenuService.create_menu_item(current_user["outlet_id"], data)
    return APIResponse(success=True, message="Menu item created successfully", data=result)


@router.put("/items/{item_id}", response_model=APIResponse)
async def update_menu_item(
    item_id: str,
    data: MenuItemUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Update a menu item"""
    result = await KDSMenuService.update_menu_item(item_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Menu item updated successfully", data=result)


@router.delete("/items/{item_id}", response_model=APIResponse)
async def delete_menu_item(
    item_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Delete a menu item"""
    await KDSMenuService.delete_menu_item(item_id, current_user["outlet_id"])
    return APIResponse(success=True, message="Menu item deleted successfully")
