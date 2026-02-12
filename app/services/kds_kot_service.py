from typing import List, Dict
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.kds import KOTCreate, KOTStatusUpdate
from datetime import datetime, timezone, timedelta


def _get_ist_now() -> str:
    IST = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(IST).isoformat()


def _get_ist_start_of_day_utc() -> str:
    utc_now = datetime.now(timezone.utc)
    ist = utc_now + timedelta(hours=5, minutes=30)
    start_of_day_ist = ist.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_day_utc = start_of_day_ist - timedelta(hours=5, minutes=30)
    return start_of_day_utc.isoformat()


class KDSKotService:

    @staticmethod
    async def get_today_kots(outlet_id: str) -> List[Dict]:
        """Get today's active KOTs for an outlet (excludes served)"""
        start_utc = _get_ist_start_of_day_utc()

        response = supabase.table("kds_kots").select("*").eq(
            "outlet_id", outlet_id
        ).gte(
            "created_at", start_utc
        ).neq(
            "kot_status", "served"
        ).order("created_at").execute()

        kots = response.data

        # Load items and order info for each KOT
        for kot in kots:
            # Load KOT items
            items_response = supabase.table("kds_kot_items").select("*").eq(
                "kot_id", kot["id"]
            ).order("created_at").execute()
            kot["items"] = items_response.data

            # Load order info
            if kot.get("order_id"):
                order_response = supabase.table("kds_orders").select("*").eq(
                    "id", kot["order_id"]
                ).execute()
                kot["order"] = order_response.data[0] if order_response.data else None

        return kots

    @staticmethod
    async def get_table_kots(table_id: str, outlet_id: str) -> List[Dict]:
        """Get KOTs for a specific table's active order (scoped to outlet)"""
        # Find active order for the table
        order_response = supabase.table("kds_orders").select("id").eq(
            "table_id", table_id
        ).eq("outlet_id", outlet_id).in_(
            "order_status", ["new", "preparing", "ready"]
        ).limit(1).execute()

        if not order_response.data:
            return []

        order_id = order_response.data[0]["id"]

        # Get KOTs for this order
        kots_response = supabase.table("kds_kots").select("*").eq(
            "order_id", order_id
        ).neq(
            "kot_status", "served"
        ).order("created_at", desc=True).execute()

        kots = kots_response.data

        # Load items for each KOT
        for kot in kots:
            items_response = supabase.table("kds_kot_items").select("*").eq(
                "kot_id", kot["id"]
            ).execute()
            kot["items"] = items_response.data

        return kots

    @staticmethod
    async def create_kot(outlet_id: str, data: KOTCreate) -> Dict:
        """Create a new KOT with items"""
        try:
            # Get next KOT number via RPC
            kot_number_response = supabase.rpc(
                "get_next_kot_number",
                {"p_outlet_id": outlet_id}
            ).execute()

            kot_number = str(kot_number_response.data)

            # Insert KOT
            kot_response = supabase.table("kds_kots").insert({
                "outlet_id": outlet_id,
                "order_id": data.order_id,
                "kot_number": kot_number,
                "kot_status": "pending",
            }).execute()

            if not kot_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create KOT"
                )

            kot = kot_response.data[0]
            kot_id = kot["id"]

            # Insert KOT items
            items_data = [{
                "kot_id": kot_id,
                "menu_item_id": item.menu_item_id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "is_veg": item.is_veg,
                "special_instructions": item.special_instructions,
            } for item in data.items]

            supabase.table("kds_kot_items").insert(items_data).execute()

            kot["items"] = items_data
            return kot

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create KOT: {str(e)}"
            )

    @staticmethod
    async def update_kot_status(kot_id: str, outlet_id: str, data: KOTStatusUpdate) -> Dict:
        """Update KOT status (scoped to outlet)"""
        update_data = {"kot_status": data.kot_status}

        if data.kot_status == "ready":
            update_data["ready_at"] = _get_ist_now()
        elif data.kot_status == "served":
            update_data["served_at"] = _get_ist_now()

        response = supabase.table("kds_kots").update(
            update_data
        ).eq("id", kot_id).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOT not found"
            )

        return response.data[0]
