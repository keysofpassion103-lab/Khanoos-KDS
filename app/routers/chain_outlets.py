from fastapi import APIRouter, Depends, status
from app.schemas.chain_outlet import ChainOutletCreate, ChainOutletUpdate
from app.schemas.response import APIResponse
from app.services.chain_outlet_service import ChainOutletService
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/chain-outlets", tags=["Chain Outlets"])


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_chain_outlet(
    data: ChainOutletCreate,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Create a new chain outlet (Admin only)"""

    result = await ChainOutletService.create(data, created_by=current_admin["id"])

    return APIResponse(
        success=True,
        message="Chain outlet created successfully",
        data=result
    )


@router.get("", response_model=APIResponse)
async def get_all_chain_outlets(current_admin: dict = Depends(get_current_admin_user)):
    """Get all chain outlets (Admin only)"""

    result = await ChainOutletService.get_all()

    return APIResponse(
        success=True,
        data=result
    )


@router.get("/{chain_id}", response_model=APIResponse)
async def get_chain_outlet(
    chain_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get chain outlet by ID (Admin only)"""

    result = await ChainOutletService.get_by_id(chain_id)

    return APIResponse(
        success=True,
        data=result
    )


@router.put("/{chain_id}", response_model=APIResponse)
async def update_chain_outlet(
    chain_id: str,
    data: ChainOutletUpdate,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Update chain outlet (Admin only)"""

    result = await ChainOutletService.update(chain_id, data)

    return APIResponse(
        success=True,
        message="Chain outlet updated successfully",
        data=result
    )


@router.delete("/{chain_id}", response_model=APIResponse)
async def delete_chain_outlet(
    chain_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Delete chain outlet (Admin only, soft delete)"""

    await ChainOutletService.delete(chain_id)

    return APIResponse(
        success=True,
        message="Chain outlet deleted successfully"
    )


@router.get("/{chain_id}/outlets", response_model=APIResponse)
async def get_chain_outlets_list(
    chain_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get all single outlets belonging to a chain (Admin only)"""

    result = await ChainOutletService.get_outlets(chain_id)

    return APIResponse(
        success=True,
        data=result
    )
