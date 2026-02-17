from typing import List, Dict, Optional
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.subscription import RenewalRequest
from app.services.activity_log_service import ActivityLogService
import logging

logger = logging.getLogger(__name__)


class SubscriptionService:

    @staticmethod
    async def get_all(outlet_id: Optional[str] = None, chain_id: Optional[str] = None,
                      payment_status: Optional[str] = None) -> List[Dict]:
        """Get subscriptions with optional filters"""

        query = supabase.table("subscriptions").select("*")

        if outlet_id:
            query = query.eq("outlet_id", outlet_id)
        if chain_id:
            query = query.eq("chain_id", chain_id)
        if payment_status:
            query = query.eq("payment_status", payment_status)

        response = query.order("created_at", desc=True).execute()
        return response.data

    @staticmethod
    async def get_by_id(subscription_id: str) -> Dict:
        """Get subscription by ID"""

        response = supabase.table("subscriptions").select("*").eq(
            "id", subscription_id
        ).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        return response.data[0]

    @staticmethod
    async def renew_outlet_plan(outlet_id: str, data: RenewalRequest) -> Dict:
        """Renew an outlet's subscription plan via RPC"""

        try:
            response = supabase.rpc(
                "renew_outlet_plan",
                {
                    "p_outlet_id": outlet_id,
                    "p_plan_id": data.plan_id,
                    "p_amount_paid": float(data.amount_paid)
                }
            ).execute()

            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]

                if result.get("success") is False:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result.get("message", "Failed to renew outlet plan")
                    )

                await ActivityLogService.log_activity(
                    action="outlet_plan_renewed",
                    outlet_id=outlet_id,
                    details={"plan_id": data.plan_id, "amount_paid": float(data.amount_paid)}
                )

                return {
                    "success": result.get("success", True),
                    "message": result.get("message", "Outlet plan renewed successfully"),
                    "new_end_date": result.get("new_end_date")
                }
            else:
                logger.warning(f"RPC renew_outlet_plan returned no data for outlet {outlet_id}")
                return {
                    "success": True,
                    "message": "Outlet plan renewed successfully",
                    "new_end_date": None
                }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to renew outlet plan: {str(e)}"
            )

    @staticmethod
    async def renew_chain_plan(chain_id: str, data: RenewalRequest) -> Dict:
        """Renew a chain's subscription plan via RPC"""

        try:
            response = supabase.rpc(
                "renew_chain_plan",
                {
                    "p_chain_id": chain_id,
                    "p_plan_id": data.plan_id,
                    "p_amount_paid": float(data.amount_paid)
                }
            ).execute()

            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]

                if result.get("success") is False:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result.get("message", "Failed to renew chain plan")
                    )

                await ActivityLogService.log_activity(
                    action="chain_plan_renewed",
                    chain_id=chain_id,
                    details={"plan_id": data.plan_id, "amount_paid": float(data.amount_paid)}
                )

                return {
                    "success": result.get("success", True),
                    "message": result.get("message", "Chain plan renewed successfully"),
                    "new_end_date": result.get("new_end_date")
                }
            else:
                logger.warning(f"RPC renew_chain_plan returned no data for chain {chain_id}")
                return {
                    "success": True,
                    "message": "Chain plan renewed successfully",
                    "new_end_date": None
                }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to renew chain plan: {str(e)}"
            )

    @staticmethod
    async def check_expired_subscriptions() -> Dict:
        """Check and update expired subscriptions via RPC"""

        try:
            response = supabase.rpc("check_expired_subscriptions", {}).execute()
            logger.info(f"check_expired_subscriptions RPC result: {response.data}")

            return {
                "success": True,
                "message": "Expired subscriptions checked and updated",
                "result": response.data
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check expired subscriptions: {str(e)}"
            )
