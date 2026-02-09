from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.schemas.subscription import RenewalRequest
from app.schemas.response import APIResponse
from app.services.subscription_service import SubscriptionService
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("", response_model=APIResponse)
async def get_subscriptions(
    outlet_id: Optional[str] = Query(None),
    chain_id: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get subscriptions with optional filters (Admin only)"""

    result = await SubscriptionService.get_all(
        outlet_id=outlet_id,
        chain_id=chain_id,
        payment_status=payment_status
    )

    return APIResponse(
        success=True,
        data=result
    )


@router.get("/{subscription_id}", response_model=APIResponse)
async def get_subscription(
    subscription_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get subscription by ID (Admin only)"""

    result = await SubscriptionService.get_by_id(subscription_id)

    return APIResponse(
        success=True,
        data=result
    )


@router.post("/outlet/{outlet_id}/renew", response_model=APIResponse)
async def renew_outlet_plan(
    outlet_id: str,
    data: RenewalRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Renew an outlet's subscription plan (Admin only)"""

    result = await SubscriptionService.renew_outlet_plan(outlet_id, data)

    return APIResponse(
        success=True,
        message="Outlet plan renewed successfully",
        data=result
    )


@router.post("/chain/{chain_id}/renew", response_model=APIResponse)
async def renew_chain_plan(
    chain_id: str,
    data: RenewalRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Renew a chain's subscription plan (Admin only)"""

    result = await SubscriptionService.renew_chain_plan(chain_id, data)

    return APIResponse(
        success=True,
        message="Chain plan renewed successfully",
        data=result
    )


@router.post("/check-expired", response_model=APIResponse)
async def check_expired_subscriptions(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Check and update expired subscriptions (Admin only)"""

    result = await SubscriptionService.check_expired_subscriptions()

    return APIResponse(
        success=True,
        message="Expired subscriptions checked",
        data=result
    )
