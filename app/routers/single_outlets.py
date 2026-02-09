from fastapi import APIRouter, Depends, status
from app.schemas.single_outlet import SingleOutletCreate, SingleOutletUpdate
from app.schemas.response import APIResponse
from app.services.single_outlet_service import SingleOutletService
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/outlets", tags=["Single Outlets"])


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_outlet(
    data: SingleOutletCreate,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Create a new single outlet (Admin only)"""

    result = await SingleOutletService.create(data, created_by=current_admin["id"])

    return APIResponse(
        success=True,
        message="Outlet created successfully",
        data=result
    )


@router.get("", response_model=APIResponse)
async def get_all_outlets(current_admin: dict = Depends(get_current_admin_user)):
    """Get all single outlets (Admin only)"""

    result = await SingleOutletService.get_all()

    return APIResponse(
        success=True,
        data=result
    )


@router.get("/{outlet_id}", response_model=APIResponse)
async def get_outlet(
    outlet_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get single outlet by ID (Admin only)"""

    result = await SingleOutletService.get_by_id(outlet_id)

    return APIResponse(
        success=True,
        data=result
    )


@router.put("/{outlet_id}", response_model=APIResponse)
async def update_outlet(
    outlet_id: str,
    data: SingleOutletUpdate,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Update single outlet (Admin only)"""

    result = await SingleOutletService.update(outlet_id, data)

    return APIResponse(
        success=True,
        message="Outlet updated successfully",
        data=result
    )


@router.delete("/{outlet_id}", response_model=APIResponse)
async def delete_outlet(
    outlet_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Delete single outlet (Admin only, soft delete)"""

    await SingleOutletService.delete(outlet_id)

    return APIResponse(
        success=True,
        message="Outlet deleted successfully"
    )


@router.get("/{outlet_id}/status", response_model=APIResponse)
async def check_outlet_status(
    outlet_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Check outlet status including subscription (Admin only)"""

    result = await SingleOutletService.check_status(outlet_id)

    return APIResponse(
        success=True,
        data=result
    )
