from typing import List, Dict
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.plan_type import PlanTypeCreate, PlanTypeUpdate
from app.services.activity_log_service import ActivityLogService


class PlanTypeService:

    @staticmethod
    async def create(data: PlanTypeCreate) -> Dict:
        """Create a new plan type"""

        # Check if plan name already exists
        existing = supabase.table("plan_types").select("id").eq(
            "name", data.name
        ).execute()

        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A plan with this name already exists"
            )

        insert_data = data.dict()
        # Convert Decimal to float for JSON serialization
        if insert_data.get("price") is not None:
            insert_data["price"] = float(insert_data["price"])

        response = supabase.table("plan_types").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create plan type"
            )

        plan = response.data[0]
        await ActivityLogService.log_activity(
            action="plan_created",
            details={"plan_name": data.name, "plan_id": plan["id"]}
        )

        return plan

    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all plan types"""

        response = supabase.table("plan_types").select("*").execute()
        return response.data

    @staticmethod
    async def get_active() -> List[Dict]:
        """Get all active plan types"""

        response = supabase.table("plan_types").select("*").eq(
            "is_active", True
        ).execute()
        return response.data

    @staticmethod
    async def get_by_id(plan_id: str) -> Dict:
        """Get plan type by ID"""

        response = supabase.table("plan_types").select("*").eq(
            "id", plan_id
        ).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan type not found"
            )

        return response.data[0]

    @staticmethod
    async def update(plan_id: str, data: PlanTypeUpdate) -> Dict:
        """Update plan type"""

        update_data = data.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        # Convert Decimal to float for JSON serialization
        if update_data.get("price") is not None:
            update_data["price"] = float(update_data["price"])

        response = supabase.table("plan_types").update(
            update_data
        ).eq("id", plan_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan type not found"
            )

        await ActivityLogService.log_activity(
            action="plan_updated",
            details={"plan_id": plan_id, "updated_fields": list(update_data.keys())}
        )

        return response.data[0]

    @staticmethod
    async def delete(plan_id: str) -> None:
        """Soft delete plan type"""

        response = supabase.table("plan_types").update(
            {"is_active": False}
        ).eq("id", plan_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan type not found"
            )

        await ActivityLogService.log_activity(
            action="plan_deleted",
            details={"plan_id": plan_id}
        )
