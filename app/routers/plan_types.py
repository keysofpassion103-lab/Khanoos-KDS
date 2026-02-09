from fastapi import APIRouter, Depends, status
from app.schemas.plan_type import PlanTypeCreate, PlanTypeUpdate
from app.schemas.response import APIResponse
from app.services.plan_type_service import PlanTypeService
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/plan-types", tags=["Plan Types"])


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_plan_type(
    data: PlanTypeCreate,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Create a new plan type (Admin only)"""

    result = await PlanTypeService.create(data)

    return APIResponse(
        success=True,
        message="Plan type created successfully",
        data=result
    )


@router.get("", response_model=APIResponse)
async def get_all_plan_types():
    """Get all active plan types (Public)"""

    result = await PlanTypeService.get_active()

    return APIResponse(
        success=True,
        data=result
    )


@router.get("/all", response_model=APIResponse)
async def get_all_plans_admin(current_admin: dict = Depends(get_current_admin_user)):
    """Get all plan types including inactive (Admin only)"""

    result = await PlanTypeService.get_all()

    return APIResponse(
        success=True,
        data=result
    )


@router.get("/{plan_id}", response_model=APIResponse)
async def get_plan_type(plan_id: str):
    """Get plan type by ID (Public)"""

    result = await PlanTypeService.get_by_id(plan_id)

    return APIResponse(
        success=True,
        data=result
    )


@router.put("/{plan_id}", response_model=APIResponse)
async def update_plan_type(
    plan_id: str,
    data: PlanTypeUpdate,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Update plan type (Admin only)"""

    result = await PlanTypeService.update(plan_id, data)

    return APIResponse(
        success=True,
        message="Plan type updated successfully",
        data=result
    )


@router.delete("/{plan_id}", response_model=APIResponse)
async def delete_plan_type(
    plan_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Delete plan type (Admin only, soft delete)"""

    await PlanTypeService.delete(plan_id)

    return APIResponse(
        success=True,
        message="Plan type deleted successfully"
    )
