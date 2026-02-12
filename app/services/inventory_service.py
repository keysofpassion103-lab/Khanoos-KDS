from typing import List, Dict, Optional
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.inventory import (
    InventoryCategoryCreate, InventoryCategoryUpdate,
    VendorCreate, VendorUpdate,
    InventoryItemCreate, InventoryItemUpdate, StockUpdate,
    RecipeItemCreate, RecipeItemUpdate,
    TransactionCreate,
)


class InventoryService:

    # ═══════════════════════════════════════════════════════════════════════
    # INVENTORY CATEGORIES
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_categories(outlet_id: str) -> List[Dict]:
        response = supabase.table("kds_inventory_categories").select("*").eq(
            "outlet_id", outlet_id
        ).eq("is_active", True).order("display_order").execute()
        return response.data

    @staticmethod
    async def create_category(outlet_id: str, data: InventoryCategoryCreate) -> Dict:
        insert_data = {
            "outlet_id": outlet_id,
            "category_name": data.category_name,
            "description": data.description,
            "display_order": data.display_order,
        }
        response = supabase.table("kds_inventory_categories").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create category")
        return response.data[0]

    @staticmethod
    async def update_category(category_id: str, outlet_id: str, data: InventoryCategoryUpdate) -> Dict:
        update_data = data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
        response = supabase.table("kds_inventory_categories").update(update_data).eq(
            "id", category_id
        ).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return response.data[0]

    @staticmethod
    async def delete_category(category_id: str, outlet_id: str) -> None:
        response = supabase.table("kds_inventory_categories").delete().eq(
            "id", category_id
        ).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # ═══════════════════════════════════════════════════════════════════════
    # VENDORS
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_vendors(outlet_id: str) -> List[Dict]:
        response = supabase.table("kds_vendors").select("*").eq(
            "outlet_id", outlet_id
        ).eq("is_active", True).order("vendor_name").execute()
        return response.data

    @staticmethod
    async def create_vendor(outlet_id: str, data: VendorCreate) -> Dict:
        insert_data = {
            "outlet_id": outlet_id,
            "vendor_name": data.vendor_name,
            "contact_person": data.contact_person,
            "email": data.email,
            "phone": data.phone,
            "address": data.address,
        }
        response = supabase.table("kds_vendors").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create vendor")
        return response.data[0]

    @staticmethod
    async def update_vendor(vendor_id: str, outlet_id: str, data: VendorUpdate) -> Dict:
        update_data = data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
        response = supabase.table("kds_vendors").update(update_data).eq(
            "id", vendor_id
        ).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        return response.data[0]

    @staticmethod
    async def delete_vendor(vendor_id: str, outlet_id: str) -> None:
        response = supabase.table("kds_vendors").delete().eq(
            "id", vendor_id
        ).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    # ═══════════════════════════════════════════════════════════════════════
    # INVENTORY ITEMS
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_items(outlet_id: str) -> List[Dict]:
        response = supabase.table("kds_inventory_items").select("*").eq(
            "outlet_id", outlet_id
        ).eq("is_active", True).order("item_name").execute()
        return response.data

    @staticmethod
    async def get_item(item_id: str, outlet_id: str) -> Dict:
        response = supabase.table("kds_inventory_items").select("*").eq(
            "id", item_id
        ).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
        return response.data[0]

    @staticmethod
    async def create_item(outlet_id: str, data: InventoryItemCreate) -> Dict:
        insert_data = {
            "outlet_id": outlet_id,
            "category_id": data.category_id,
            "vendor_id": data.vendor_id,
            "item_name": data.item_name,
            "description": data.description,
            "unit": data.unit,
            "current_stock": data.current_stock,
            "minimum_stock": data.minimum_stock,
            "maximum_stock": data.maximum_stock,
            "reorder_quantity": data.reorder_quantity,
            "unit_cost": data.unit_cost,
        }
        if data.expiry_date:
            insert_data["expiry_date"] = data.expiry_date.isoformat()

        response = supabase.table("kds_inventory_items").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create item")
        return response.data[0]

    @staticmethod
    async def update_item(item_id: str, outlet_id: str, data: InventoryItemUpdate) -> Dict:
        update_data = data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")

        # Handle date serialization
        if "expiry_date" in update_data and update_data["expiry_date"] is not None:
            update_data["expiry_date"] = update_data["expiry_date"].isoformat()

        response = supabase.table("kds_inventory_items").update(update_data).eq(
            "id", item_id
        ).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return response.data[0]

    @staticmethod
    async def update_stock(item_id: str, outlet_id: str, data: StockUpdate) -> Dict:
        response = supabase.table("kds_inventory_items").update(
            {"current_stock": data.current_stock}
        ).eq("id", item_id).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return response.data[0]

    @staticmethod
    async def delete_item(item_id: str, outlet_id: str) -> None:
        response = supabase.table("kds_inventory_items").delete().eq(
            "id", item_id
        ).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # ═══════════════════════════════════════════════════════════════════════
    # RECIPE ITEMS
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def _verify_menu_item_belongs_to_outlet(menu_item_id: str, outlet_id: str) -> None:
        """Helper: verify a menu item belongs to the given outlet"""
        response = supabase.table("kds_menu_items").select("id").eq(
            "id", menu_item_id
        ).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found for this outlet"
            )

    @staticmethod
    async def get_recipe_items(menu_item_id: str, outlet_id: str) -> List[Dict]:
        # Verify menu item belongs to outlet
        await InventoryService._verify_menu_item_belongs_to_outlet(menu_item_id, outlet_id)
        response = supabase.table("kds_recipe_items").select("*").eq(
            "menu_item_id", menu_item_id
        ).order("created_at").execute()
        return response.data

    @staticmethod
    async def create_recipe_item(data: RecipeItemCreate, outlet_id: str) -> Dict:
        # Verify menu item belongs to outlet
        await InventoryService._verify_menu_item_belongs_to_outlet(data.menu_item_id, outlet_id)
        insert_data = {
            "menu_item_id": data.menu_item_id,
            "inventory_item_id": data.inventory_item_id,
            "quantity_required": data.quantity_required,
            "unit": data.unit,
            "notes": data.notes,
        }
        response = supabase.table("kds_recipe_items").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create recipe item")
        return response.data[0]

    @staticmethod
    async def update_recipe_item(recipe_item_id: str, outlet_id: str, data: RecipeItemUpdate) -> Dict:
        # Verify the recipe item's menu_item belongs to outlet
        recipe_response = supabase.table("kds_recipe_items").select("menu_item_id").eq(
            "id", recipe_item_id
        ).execute()
        if not recipe_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe item not found")
        await InventoryService._verify_menu_item_belongs_to_outlet(
            recipe_response.data[0]["menu_item_id"], outlet_id
        )

        update_data = data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
        response = supabase.table("kds_recipe_items").update(update_data).eq("id", recipe_item_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe item not found")
        return response.data[0]

    @staticmethod
    async def delete_recipe_item(recipe_item_id: str, outlet_id: str) -> None:
        # Verify the recipe item's menu_item belongs to outlet
        recipe_response = supabase.table("kds_recipe_items").select("menu_item_id").eq(
            "id", recipe_item_id
        ).execute()
        if not recipe_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe item not found")
        await InventoryService._verify_menu_item_belongs_to_outlet(
            recipe_response.data[0]["menu_item_id"], outlet_id
        )

        response = supabase.table("kds_recipe_items").delete().eq("id", recipe_item_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe item not found")

    # ═══════════════════════════════════════════════════════════════════════
    # TRANSACTIONS
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_transactions(
        outlet_id: str,
        inventory_item_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        query = supabase.table("kds_inventory_transactions").select("*").eq(
            "outlet_id", outlet_id
        )
        if inventory_item_id:
            query = query.eq("inventory_item_id", inventory_item_id)

        response = query.order("transaction_date", desc=True).limit(limit).execute()
        return response.data

    @staticmethod
    async def create_transaction(outlet_id: str, data: TransactionCreate, user_id: Optional[str] = None) -> Dict:
        insert_data = {
            "outlet_id": outlet_id,
            "inventory_item_id": data.inventory_item_id,
            "transaction_type": data.transaction_type,
            "quantity": data.quantity,
            "unit": data.unit,
            "reference_type": data.reference_type,
            "reference_id": data.reference_id,
            "notes": data.notes,
        }
        if user_id:
            insert_data["created_by"] = user_id

        response = supabase.table("kds_inventory_transactions").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create transaction")

        # Update stock via RPC based on transaction type
        if data.transaction_type in ("purchase", "adjustment"):
            # Increase stock
            supabase.rpc("update_inventory_stock", {
                "p_item_id": data.inventory_item_id,
                "p_quantity_change": data.quantity,
            }).execute()
        elif data.transaction_type in ("usage", "waste"):
            # Decrease stock
            supabase.rpc("update_inventory_stock", {
                "p_item_id": data.inventory_item_id,
                "p_quantity_change": -data.quantity,
            }).execute()

        return response.data[0]

    # ═══════════════════════════════════════════════════════════════════════
    # ALERTS
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_alerts(outlet_id: str, unread_only: bool = False) -> List[Dict]:
        query = supabase.table("kds_inventory_alerts").select("*").eq("outlet_id", outlet_id)
        if unread_only:
            query = query.eq("is_read", False)
        response = query.order("created_at", desc=True).execute()
        return response.data

    @staticmethod
    async def mark_alert_read(alert_id: str, outlet_id: str) -> Dict:
        response = supabase.table("kds_inventory_alerts").update(
            {"is_read": True}
        ).eq("id", alert_id).eq("outlet_id", outlet_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        return response.data[0]

    @staticmethod
    async def mark_all_alerts_read(outlet_id: str) -> Dict:
        supabase.table("kds_inventory_alerts").update(
            {"is_read": True}
        ).eq("outlet_id", outlet_id).eq("is_read", False).execute()
        return {"message": "All alerts marked as read"}

    # ═══════════════════════════════════════════════════════════════════════
    # RPC FUNCTION WRAPPERS
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_inventory_summary(outlet_id: str) -> Dict:
        """Get inventory summary via RPC"""
        try:
            response = supabase.rpc(
                "get_inventory_summary",
                {"p_outlet_id": outlet_id}
            ).execute()

            if response.data and len(response.data) > 0:
                result = response.data[0] if isinstance(response.data, list) else response.data
                return result

            return {
                "total_items": 0,
                "low_stock_items": 0,
                "out_of_stock_items": 0,
                "about_to_expire_items": 0,
                "expired_items": 0,
                "total_value": 0,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get inventory summary: {str(e)}"
            )

    @staticmethod
    async def get_recipe_cost(menu_item_id: str, outlet_id: str) -> Dict:
        """Get recipe cost via RPC (verifies menu item belongs to outlet)"""
        await InventoryService._verify_menu_item_belongs_to_outlet(menu_item_id, outlet_id)
        try:
            response = supabase.rpc(
                "get_recipe_cost",
                {"p_menu_item_id": menu_item_id}
            ).execute()

            cost = response.data if response.data is not None else 0
            if isinstance(cost, list) and len(cost) > 0:
                cost = cost[0]
            return {"menu_item_id": menu_item_id, "recipe_cost": float(cost)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get recipe cost: {str(e)}"
            )

    @staticmethod
    async def can_prepare_item(menu_item_id: str, quantity: int = 1, outlet_id: str = None) -> Dict:
        """Check if item can be prepared via RPC"""
        if outlet_id:
            await InventoryService._verify_menu_item_belongs_to_outlet(menu_item_id, outlet_id)
        try:
            response = supabase.rpc(
                "can_prepare_item",
                {"p_menu_item_id": menu_item_id, "p_quantity": quantity}
            ).execute()

            if response.data and len(response.data) > 0:
                result = response.data[0] if isinstance(response.data, list) else response.data
                return {
                    "can_prepare": result.get("can_prepare", False),
                    "missing_ingredients": result.get("missing_ingredients", []),
                }

            return {"can_prepare": True, "missing_ingredients": []}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check preparation: {str(e)}"
            )

    @staticmethod
    async def get_recipe_with_conversion(menu_item_id: str, outlet_id: str) -> List[Dict]:
        """Get recipe details with unit conversion via RPC"""
        await InventoryService._verify_menu_item_belongs_to_outlet(menu_item_id, outlet_id)
        try:
            response = supabase.rpc(
                "get_recipe_with_conversion",
                {"p_menu_item_id": menu_item_id}
            ).execute()

            return response.data if response.data else []
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get recipe conversion: {str(e)}"
            )

    @staticmethod
    async def get_low_stock_items(outlet_id: str) -> List[Dict]:
        """Get low stock items via RPC"""
        try:
            response = supabase.rpc(
                "get_low_stock_items",
                {"p_outlet_id": outlet_id}
            ).execute()

            return response.data if response.data else []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get low stock items: {str(e)}"
            )

    @staticmethod
    async def deduct_inventory_for_order(order_id: str, outlet_id: str) -> Dict:
        """Deduct inventory for order via RPC (verifies order belongs to outlet)"""
        # Verify order belongs to outlet
        order_check = supabase.table("kds_orders").select("id").eq(
            "id", order_id
        ).eq("outlet_id", outlet_id).execute()
        if not order_check.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        try:
            response = supabase.rpc(
                "deduct_inventory_for_order",
                {"p_order_id": order_id}
            ).execute()

            if response.data and len(response.data) > 0:
                result = response.data[0] if isinstance(response.data, list) else response.data
                return {
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "failed_items": result.get("failed_items", []),
                }

            return {"success": False, "message": "No response from database", "failed_items": []}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deduct inventory: {str(e)}"
            )

    @staticmethod
    async def validate_order_inventory(order_items: list) -> Dict:
        """Validate order inventory via RPC"""
        try:
            response = supabase.rpc(
                "validate_order_inventory",
                {"p_order_items": order_items}
            ).execute()

            if response.data and len(response.data) > 0:
                result = response.data[0] if isinstance(response.data, list) else response.data
                return {
                    "is_valid": result.get("is_valid", False),
                    "invalid_items": result.get("invalid_items", []),
                }

            return {"is_valid": True, "invalid_items": []}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to validate inventory: {str(e)}"
            )
