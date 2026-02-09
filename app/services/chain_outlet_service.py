import uuid
from typing import List, Dict
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.chain_outlet import ChainOutletCreate, ChainOutletUpdate


class ChainOutletService:

    @staticmethod
    async def create(data: ChainOutletCreate, created_by: str = None) -> Dict:
        """Create a new chain outlet with generated master license key"""

        # Verify plan exists
        plan = supabase.table("plan_types").select("id").eq(
            "id", data.plan_id
        ).execute()

        if not plan.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan ID"
            )

        try:
            master_license_key = str(uuid.uuid4())

            insert_data = data.dict()
            insert_data["master_license_key"] = master_license_key
            insert_data["is_active"] = False
            insert_data["master_key_used"] = False
            if created_by:
                insert_data["created_by"] = created_by

            response = supabase.table("chain_outlets").insert(insert_data).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create chain outlet"
                )

            chain = response.data[0]

            # Create entry in license_keys table
            supabase.table("license_keys").insert({
                "license_key": master_license_key,
                "key_type": "master",
                "chain_id": chain["id"],
                "is_used": False
            }).execute()

            return chain

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create chain outlet: {str(e)}"
            )

    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all chain outlets"""

        response = supabase.table("chain_outlets").select("*").execute()
        return response.data

    @staticmethod
    async def get_by_id(chain_id: str) -> Dict:
        """Get chain outlet by ID"""

        response = supabase.table("chain_outlets").select("*").eq(
            "id", chain_id
        ).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chain outlet not found"
            )

        return response.data[0]

    @staticmethod
    async def update(chain_id: str, data: ChainOutletUpdate) -> Dict:
        """Update chain outlet"""

        update_data = data.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        response = supabase.table("chain_outlets").update(
            update_data
        ).eq("id", chain_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chain outlet not found"
            )

        return response.data[0]

    @staticmethod
    async def delete(chain_id: str) -> None:
        """Soft delete chain outlet"""

        response = supabase.table("chain_outlets").update(
            {"is_active": False}
        ).eq("id", chain_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chain outlet not found"
            )

    @staticmethod
    async def get_outlets(chain_id: str) -> List[Dict]:
        """Get all single outlets belonging to a chain"""

        # Verify chain exists
        chain = supabase.table("chain_outlets").select("id").eq(
            "id", chain_id
        ).execute()

        if not chain.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chain outlet not found"
            )

        response = supabase.table("single_outlets").select("*").eq(
            "chain_id", chain_id
        ).execute()

        return response.data
