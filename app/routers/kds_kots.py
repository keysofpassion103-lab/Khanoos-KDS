from fastapi import APIRouter, Depends, status
from app.schemas.kds import KOTCreate, KOTStatusUpdate
from app.schemas.response import APIResponse
from app.services.kds_kot_service import KDSKotService
from app.auth.dependencies import get_current_outlet_user

router = APIRouter(prefix="/kds/kots", tags=["KDS KOTs"])


@router.get("", response_model=APIResponse)
async def get_today_kots(current_user: dict = Depends(get_current_outlet_user)):
    """Get today's active KOTs for the current outlet"""
    result = await KDSKotService.get_today_kots(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.get("/served", response_model=APIResponse)
async def get_served_kots(current_user: dict = Depends(get_current_outlet_user)):
    """Get today's served KOTs for the current outlet"""
    result = await KDSKotService.get_served_kots(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.get("/table/{table_id}", response_model=APIResponse)
async def get_table_kots(
    table_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Get KOTs for a specific table's active order"""
    result = await KDSKotService.get_table_kots(table_id, current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_kot(
    data: KOTCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Create a new KOT with items"""
    result = await KDSKotService.create_kot(current_user["outlet_id"], data)
    return APIResponse(success=True, message="KOT created successfully", data=result)


@router.patch("/{kot_id}/status", response_model=APIResponse)
async def update_kot_status(
    kot_id: str,
    data: KOTStatusUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Update KOT status"""
    result = await KDSKotService.update_kot_status(kot_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="KOT status updated", data=result)
