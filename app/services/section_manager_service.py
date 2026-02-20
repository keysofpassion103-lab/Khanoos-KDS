"""
Service layer for Section Manager operations:
- CRUD for section managers (outlet owner only)
- Section-scoped data fetching (tables, orders, KOTs)
"""

from typing import List, Dict
from fastapi import HTTPException, status
from app.database import supabase, get_fresh_supabase_client
from app.schemas.section_manager import SectionManagerCreate, SectionManagerUpdate
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


def _get_ist_start_of_day_utc() -> str:
    """Get start of today in IST, converted to UTC ISO string."""
    utc_now = datetime.now(timezone.utc)
    ist = utc_now + timedelta(hours=5, minutes=30)
    start_of_day_ist = ist.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_day_utc = start_of_day_ist - timedelta(hours=5, minutes=30)
    return start_of_day_utc.isoformat()


class SectionManagerService:

    # ── CRUD (outlet owner) ──────────────────────────────────────────────────

    @staticmethod
    async def get_section_managers(outlet_id: str) -> List[Dict]:
        """Get all section managers for an outlet, with section name joined."""
        response = supabase.table("section_managers").select(
            "*, kds_sections(section_name)"
        ).eq("outlet_id", outlet_id).order("created_at").execute()
        return response.data or []

    @staticmethod
    async def create_section_manager(outlet_id: str, data: SectionManagerCreate) -> Dict:
        """
        Create a section manager:
        1. Verify section belongs to outlet
        2. Check section not already assigned to another active manager
        3. Create Supabase Auth user with section_manager metadata
        4. Insert into section_managers table
        """
        db = get_fresh_supabase_client()

        # 1. Verify section belongs to outlet
        section_resp = db.table("kds_sections").select("id, section_name").eq(
            "id", data.section_id
        ).eq("outlet_id", outlet_id).execute()

        if not section_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found in this outlet"
            )

        # 2. Check section not already assigned
        existing = db.table("section_managers").select("id").eq(
            "outlet_id", outlet_id
        ).eq("section_id", data.section_id).eq("is_active", True).execute()

        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This section already has an active manager assigned"
            )

        # 3. Create Supabase Auth user
        try:
            auth_client = get_fresh_supabase_client()
            user_response = auth_client.auth.admin.create_user({
                "email": data.email,
                "password": data.password,
                "email_confirm": True,
                "user_metadata": {
                    "user_type": "section_manager",
                    "outlet_id": outlet_id,
                    "section_id": data.section_id,
                    "full_name": data.full_name,
                }
            })
            user_id = str(user_response.user.id)
            logger.info(f"Created auth user {user_id} for section manager {data.email}")
        except Exception as e:
            err_msg = str(e).lower()
            if "already been registered" in err_msg or "already exists" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email already exists"
                )
            logger.error(f"Failed to create auth user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create auth user: {str(e)}"
            )

        # 4. Insert into section_managers table
        insert_data = {
            "outlet_id": outlet_id,
            "section_id": data.section_id,
            "user_id": user_id,
            "email": data.email,
            "full_name": data.full_name,
            "is_active": True,
        }

        db2 = get_fresh_supabase_client()
        response = db2.table("section_managers").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create section manager record"
            )

        result = response.data[0]
        result["kds_sections"] = {"section_name": section_resp.data[0]["section_name"]}
        return result

    @staticmethod
    async def update_section_manager(
        manager_id: str, outlet_id: str, data: SectionManagerUpdate
    ) -> Dict:
        """Update a section manager's details."""
        db = get_fresh_supabase_client()

        # Verify manager belongs to this outlet
        manager_resp = db.table("section_managers").select("*").eq(
            "id", manager_id
        ).eq("outlet_id", outlet_id).execute()

        if not manager_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section manager not found"
            )

        manager = manager_resp.data[0]
        update_data = {}

        if data.full_name is not None:
            update_data["full_name"] = data.full_name
        if data.is_active is not None:
            update_data["is_active"] = data.is_active
        if data.section_id is not None and data.section_id != manager["section_id"]:
            # Verify new section belongs to outlet
            section_resp = db.table("kds_sections").select("id").eq(
                "id", data.section_id
            ).eq("outlet_id", outlet_id).execute()
            if not section_resp.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="New section not found in this outlet"
                )
            # Check new section not already assigned
            existing = db.table("section_managers").select("id").eq(
                "outlet_id", outlet_id
            ).eq("section_id", data.section_id).eq("is_active", True).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New section already has an active manager"
                )
            update_data["section_id"] = data.section_id

            # Update Supabase Auth user_metadata with new section_id
            try:
                auth_client = get_fresh_supabase_client()
                auth_client.auth.admin.update_user_by_id(
                    manager["user_id"],
                    {"user_metadata": {"section_id": data.section_id}}
                )
            except Exception as e:
                logger.error(f"Failed to update auth user metadata: {e}")

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        db2 = get_fresh_supabase_client()
        response = db2.table("section_managers").update(update_data).eq(
            "id", manager_id
        ).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update section manager"
            )
        return response.data[0]

    @staticmethod
    async def delete_section_manager(manager_id: str, outlet_id: str) -> None:
        """Delete a section manager (deactivate + delete auth user)."""
        db = get_fresh_supabase_client()

        # Get manager record
        manager_resp = db.table("section_managers").select("*").eq(
            "id", manager_id
        ).eq("outlet_id", outlet_id).execute()

        if not manager_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section manager not found"
            )

        manager = manager_resp.data[0]

        # Delete auth user
        try:
            auth_client = get_fresh_supabase_client()
            auth_client.auth.admin.delete_user(manager["user_id"])
            logger.info(f"Deleted auth user {manager['user_id']} for section manager {manager['email']}")
        except Exception as e:
            logger.error(f"Failed to delete auth user: {e}")

        # Delete from section_managers table
        db2 = get_fresh_supabase_client()
        db2.table("section_managers").delete().eq(
            "id", manager_id
        ).eq("outlet_id", outlet_id).execute()

    # ── Section-scoped data fetching ─────────────────────────────────────────

    @staticmethod
    async def get_tables_by_section(outlet_id: str, section_id: str) -> List[Dict]:
        """Get tables for a specific section."""
        response = supabase.table("kds_tables").select(
            "*, kds_sections(id, section_name, display_order, is_active)"
        ).eq("outlet_id", outlet_id).eq("section_id", section_id).execute()
        return response.data or []

    @staticmethod
    async def get_orders_by_section(outlet_id: str, section_id: str) -> List[Dict]:
        """Get today's orders for tables in a specific section."""
        start_utc = _get_ist_start_of_day_utc()

        # Get table IDs for this section
        tables_resp = supabase.table("kds_tables").select("id").eq(
            "outlet_id", outlet_id
        ).eq("section_id", section_id).execute()

        table_ids = [t["id"] for t in (tables_resp.data or [])]
        if not table_ids:
            return []

        # Get orders for those tables (today only)
        orders_resp = supabase.table("kds_orders").select("*").eq(
            "outlet_id", outlet_id
        ).in_("table_id", table_ids).gte(
            "created_at", start_utc
        ).order("created_at", desc=True).execute()

        orders = orders_resp.data or []

        # Load items for each order
        for order in orders:
            items_resp = supabase.table("kds_order_items").select("*").eq(
                "order_id", order["id"]
            ).execute()
            order["items"] = items_resp.data or []

        return orders

    @staticmethod
    async def get_kots_by_section(outlet_id: str, section_id: str) -> List[Dict]:
        """Get today's active KOTs for orders in a specific section."""
        start_utc = _get_ist_start_of_day_utc()

        # Get table IDs for this section
        tables_resp = supabase.table("kds_tables").select("id").eq(
            "outlet_id", outlet_id
        ).eq("section_id", section_id).execute()

        table_ids = [t["id"] for t in (tables_resp.data or [])]
        if not table_ids:
            return []

        # Get order IDs for those tables (today only)
        orders_resp = supabase.table("kds_orders").select("id").eq(
            "outlet_id", outlet_id
        ).in_("table_id", table_ids).gte(
            "created_at", start_utc
        ).execute()

        order_ids = [o["id"] for o in (orders_resp.data or [])]
        if not order_ids:
            return []

        # Get active KOTs for those orders
        kots_resp = supabase.table("kds_kots").select("*").eq(
            "outlet_id", outlet_id
        ).in_("order_id", order_ids).neq(
            "kot_status", "served"
        ).order("created_at").execute()

        kots = kots_resp.data or []

        # Load items and order info for each KOT
        for kot in kots:
            items_resp = supabase.table("kds_kot_items").select("*").eq(
                "kot_id", kot["id"]
            ).order("created_at").execute()
            kot["items"] = items_resp.data or []

            if kot.get("order_id"):
                order_resp = supabase.table("kds_orders").select("*").eq(
                    "id", kot["order_id"]
                ).execute()
                kot["order"] = order_resp.data[0] if order_resp.data else None

        return kots

    @staticmethod
    async def get_served_kots_by_section(outlet_id: str, section_id: str) -> List[Dict]:
        """Get today's served KOTs for orders in a specific section."""
        start_utc = _get_ist_start_of_day_utc()

        tables_resp = supabase.table("kds_tables").select("id").eq(
            "outlet_id", outlet_id
        ).eq("section_id", section_id).execute()

        table_ids = [t["id"] for t in (tables_resp.data or [])]
        if not table_ids:
            return []

        orders_resp = supabase.table("kds_orders").select("id").eq(
            "outlet_id", outlet_id
        ).in_("table_id", table_ids).gte(
            "created_at", start_utc
        ).execute()

        order_ids = [o["id"] for o in (orders_resp.data or [])]
        if not order_ids:
            return []

        kots_resp = supabase.table("kds_kots").select("*").eq(
            "outlet_id", outlet_id
        ).in_("order_id", order_ids).eq(
            "kot_status", "served"
        ).order("created_at", desc=True).execute()

        kots = kots_resp.data or []

        for kot in kots:
            items_resp = supabase.table("kds_kot_items").select("*").eq(
                "kot_id", kot["id"]
            ).order("created_at").execute()
            kot["items"] = items_resp.data or []

            if kot.get("order_id"):
                order_resp = supabase.table("kds_orders").select("*").eq(
                    "id", kot["order_id"]
                ).execute()
                kot["order"] = order_resp.data[0] if order_resp.data else None

        return kots
