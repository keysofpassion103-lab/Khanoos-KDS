from typing import List, Dict
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.kds import MenuCategoryCreate, MenuCategoryUpdate, MenuItemCreate, MenuItemUpdate


class KDSMenuService:

    # ═══════════════════════════════════════════════════════════════════════
    # MENU CATEGORIES
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_categories() -> List[Dict]:
        """Get all active menu categories"""
        response = supabase.table("kds_menu_categories").select("*").eq(
            "is_active", True
        ).order("display_order").execute()
        return response.data

    @staticmethod
    async def create_category(data: MenuCategoryCreate) -> Dict:
        """Create a new menu category"""
        insert_data = {
            "name": data.name,
            "display_order": data.display_order,
            "is_active": True,
        }

        response = supabase.table("kds_menu_categories").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create category"
            )

        return response.data[0]

    @staticmethod
    async def update_category(category_id: str, data: MenuCategoryUpdate) -> Dict:
        """Update a menu category"""
        update_data = data.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        response = supabase.table("kds_menu_categories").update(
            update_data
        ).eq("id", category_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        return response.data[0]

    @staticmethod
    async def delete_category(category_id: str) -> None:
        """Delete a menu category"""
        response = supabase.table("kds_menu_categories").delete().eq(
            "id", category_id
        ).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # MENU ITEMS
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_menu_items(outlet_id: str) -> List[Dict]:
        """Get all menu items for an outlet"""
        response = supabase.table("kds_menu_items").select("*").eq(
            "outlet_id", outlet_id
        ).order("item_name").execute()
        return response.data

    @staticmethod
    async def get_menu_item(item_id: str, outlet_id: str) -> Dict:
        """Get a single menu item by ID (scoped to outlet)"""
        response = supabase.table("kds_menu_items").select("*").eq(
            "id", item_id
        ).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found"
            )

        return response.data[0]

    @staticmethod
    async def create_menu_item(outlet_id: str, data: MenuItemCreate) -> Dict:
        """Create a new menu item"""
        insert_data = {
            "outlet_id": outlet_id,
            "category_id": data.category_id,
            "item_name": data.item_name,
            "description": data.description,
            "short_code": data.short_code,
            "price": data.price,
            "is_veg": data.is_veg,
            "image_url": data.image_url,
            "is_available": True,
        }

        response = supabase.table("kds_menu_items").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create menu item"
            )

        return response.data[0]

    @staticmethod
    async def update_menu_item(item_id: str, outlet_id: str, data: MenuItemUpdate) -> Dict:
        """Update a menu item (scoped to outlet)"""
        update_data = data.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        response = supabase.table("kds_menu_items").update(
            update_data
        ).eq("id", item_id).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found"
            )

        return response.data[0]

    @staticmethod
    async def delete_menu_item(item_id: str, outlet_id: str) -> None:
        """Delete a menu item (scoped to outlet)"""
        response = supabase.table("kds_menu_items").delete().eq(
            "id", item_id
        ).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found"
            )
