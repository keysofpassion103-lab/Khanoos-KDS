from typing import List, Dict
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.kds import (
    SectionCreate, SectionUpdate,
    TableCreate, TableUpdate, TableStatusUpdate
)


class SectionTableService:

    # ═══════════════════════════════════════════════════════════════════════
    # SECTIONS
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_sections(outlet_id: str) -> List[Dict]:
        """Get all active sections for an outlet"""
        response = supabase.table("kds_sections").select("*").eq(
            "outlet_id", outlet_id
        ).eq(
            "is_active", True
        ).order("display_order").execute()
        return response.data

    @staticmethod
    async def create_section(outlet_id: str, data: SectionCreate) -> Dict:
        """Create a new section"""
        # Auto-calculate display_order if not provided
        display_order = data.display_order
        if display_order is None:
            max_order_response = supabase.table("kds_sections").select(
                "display_order"
            ).eq(
                "outlet_id", outlet_id
            ).order("display_order", desc=True).limit(1).execute()

            display_order = (max_order_response.data[0]["display_order"] + 1) if max_order_response.data else 0

        insert_data = {
            "outlet_id": outlet_id,
            "section_name": data.section_name,
            "display_order": display_order,
            "is_active": True,
        }

        response = supabase.table("kds_sections").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create section"
            )

        return response.data[0]

    @staticmethod
    async def update_section(section_id: str, outlet_id: str, data: SectionUpdate) -> Dict:
        """Update a section (scoped to outlet)"""
        update_data = data.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        response = supabase.table("kds_sections").update(
            update_data
        ).eq("id", section_id).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )

        return response.data[0]

    @staticmethod
    async def delete_section(section_id: str, outlet_id: str) -> None:
        """Delete a section (scoped to outlet, unlinks tables first)"""
        # Unlink tables from this section (scoped to outlet)
        supabase.table("kds_tables").update(
            {"section_id": None}
        ).eq("section_id", section_id).eq("outlet_id", outlet_id).execute()

        # Delete the section
        response = supabase.table("kds_sections").delete().eq(
            "id", section_id
        ).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # TABLES
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_tables(outlet_id: str) -> List[Dict]:
        """Get all tables for an outlet with section info"""
        response = supabase.table("kds_tables").select(
            "*, kds_sections(*)"
        ).eq(
            "outlet_id", outlet_id
        ).order("table_number").execute()
        return response.data

    @staticmethod
    async def create_table(outlet_id: str, data: TableCreate) -> Dict:
        """Create a new table"""
        insert_data = {
            "outlet_id": outlet_id,
            "section_id": data.section_id,
            "table_number": data.table_number,
            "capacity": data.capacity,
            "is_ac": data.is_ac,
            "status": "available",
        }

        response = supabase.table("kds_tables").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create table"
            )

        return response.data[0]

    @staticmethod
    async def update_table(table_id: str, outlet_id: str, data: TableUpdate) -> Dict:
        """Update a table (scoped to outlet)"""
        update_data = data.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        response = supabase.table("kds_tables").update(
            update_data
        ).eq("id", table_id).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found"
            )

        return response.data[0]

    @staticmethod
    async def update_table_status(table_id: str, outlet_id: str, data: TableStatusUpdate) -> Dict:
        """Update table status (scoped to outlet)"""
        response = supabase.table("kds_tables").update(
            {"status": data.status}
        ).eq("id", table_id).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found"
            )

        return response.data[0]

    @staticmethod
    async def delete_table(table_id: str, outlet_id: str) -> None:
        """Delete a table (scoped to outlet)"""
        response = supabase.table("kds_tables").delete().eq(
            "id", table_id
        ).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found"
            )
