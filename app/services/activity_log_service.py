from typing import List, Dict, Optional
from fastapi import HTTPException, status
from app.database import supabase


class ActivityLogService:

    @staticmethod
    async def get_logs(
        outlet_id: Optional[str] = None,
        chain_id: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """Get activity logs with filters and pagination"""

        query = supabase.table("activity_logs").select("*", count="exact")

        if outlet_id:
            query = query.eq("outlet_id", outlet_id)
        if chain_id:
            query = query.eq("chain_id", chain_id)
        if action:
            query = query.eq("action", action)
        if user_id:
            query = query.eq("user_id", user_id)
        if start_date:
            query = query.gte("created_at", start_date)
        if end_date:
            query = query.lte("created_at", end_date)

        # Pagination
        offset = (page - 1) * page_size
        query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

        response = query.execute()

        return {
            "logs": response.data,
            "total": response.count if response.count else len(response.data),
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    async def get_logs_by_outlet(outlet_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """Get activity logs for a specific outlet"""

        offset = (page - 1) * page_size

        response = supabase.table("activity_logs").select(
            "*", count="exact"
        ).eq(
            "outlet_id", outlet_id
        ).order(
            "created_at", desc=True
        ).range(offset, offset + page_size - 1).execute()

        return {
            "logs": response.data,
            "total": response.count if response.count else len(response.data),
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    async def log_activity(
        action: str,
        outlet_id: Optional[str] = None,
        chain_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None
    ) -> Dict:
        """Create an activity log entry"""

        try:
            insert_data = {
                "action": action,
                "outlet_id": outlet_id,
                "chain_id": chain_id,
                "user_id": user_id,
                "details": details,
                "ip_address": ip_address
            }

            response = supabase.table("activity_logs").insert(insert_data).execute()

            if not response.data:
                return {"success": False, "message": "Failed to create activity log"}

            return response.data[0]

        except Exception:
            # Activity logging should not raise exceptions
            return {"success": False, "message": "Failed to create activity log"}
