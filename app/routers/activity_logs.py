from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.schemas.response import APIResponse
from app.services.activity_log_service import ActivityLogService
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get("", response_model=APIResponse)
async def get_activity_logs(
    outlet_id: Optional[str] = Query(None),
    chain_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get activity logs with filters (Admin only)"""

    result = await ActivityLogService.get_logs(
        outlet_id=outlet_id,
        chain_id=chain_id,
        action=action,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )

    return APIResponse(
        success=True,
        data=result
    )


@router.get("/outlet/{outlet_id}", response_model=APIResponse)
async def get_outlet_activity_logs(
    outlet_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get activity logs for a specific outlet (Admin only)"""

    result = await ActivityLogService.get_logs_by_outlet(
        outlet_id=outlet_id,
        page=page,
        page_size=page_size
    )

    return APIResponse(
        success=True,
        data=result
    )
