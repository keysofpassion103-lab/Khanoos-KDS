import uuid
from typing import List, Dict
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.single_outlet import SingleOutletCreate, SingleOutletUpdate


class SingleOutletService:

    @staticmethod
    async def create(data: SingleOutletCreate, created_by: str = None) -> Dict:
        """Create a new single outlet with generated license key"""

        # Verify plan exists
        plan = supabase.table("plan_types").select("id").eq(
            "id", data.plan_id
        ).execute()

        if not plan.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan ID"
            )

        # If chain_id provided, verify chain exists
        if data.chain_id:
            chain = supabase.table("chain_outlets").select("id").eq(
                "id", data.chain_id
            ).execute()

            if not chain.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid chain ID"
                )

        try:
            license_key = str(uuid.uuid4())

            insert_data = data.dict()
            insert_data["license_key"] = license_key
            insert_data["is_active"] = False
            insert_data["license_key_used"] = False
            if created_by:
                insert_data["created_by"] = created_by

            response = supabase.table("single_outlets").insert(insert_data).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create outlet"
                )

            outlet = response.data[0]

            # Create entry in license_keys table
            key_type = "branch" if data.chain_id else "license"
            supabase.table("license_keys").insert({
                "license_key": license_key,
                "key_type": key_type,
                "outlet_id": outlet["id"],
                "chain_id": data.chain_id,
                "is_used": False
            }).execute()

            return outlet

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create outlet: {str(e)}"
            )

    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all single outlets"""

        response = supabase.table("single_outlets").select("*").execute()
        return response.data

    @staticmethod
    async def get_by_id(outlet_id: str) -> Dict:
        """Get single outlet by ID"""

        response = supabase.table("single_outlets").select("*").eq(
            "id", outlet_id
        ).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Outlet not found"
            )

        return response.data[0]

    @staticmethod
    async def update(outlet_id: str, data: SingleOutletUpdate) -> Dict:
        """Update single outlet"""

        update_data = data.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        response = supabase.table("single_outlets").update(
            update_data
        ).eq("id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Outlet not found"
            )

        return response.data[0]

    @staticmethod
    async def delete(outlet_id: str) -> None:
        """Soft delete single outlet"""

        response = supabase.table("single_outlets").update(
            {"is_active": False}
        ).eq("id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Outlet not found"
            )

    @staticmethod
    async def check_status(outlet_id: str) -> Dict:
        """Check outlet status via RPC"""

        try:
            response = supabase.rpc(
                "check_outlet_status",
                {"p_outlet_id": outlet_id}
            ).execute()

            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                return result
            else:
                return {
                    "is_active": False,
                    "plan_expired": True,
                    "days_remaining": 0,
                    "plan_end_date": None
                }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check outlet status: {str(e)}"
            )
