from fastapi import APIRouter, Depends, Query, status
from app.schemas.chain_owner import ChainOwnerSignupRequest, ChainOwnerLoginRequest
from app.schemas.response import APIResponse
from app.services.chain_owner_service import ChainOwnerService
from app.auth.dependencies import get_current_chain_owner

router = APIRouter(prefix="/chain-owner", tags=["Chain Owner"])


@router.post("/signup", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def chain_owner_signup(data: ChainOwnerSignupRequest):
    """Register a chain owner account using master license key"""
    result = await ChainOwnerService.signup(data)
    return APIResponse(
        success=True,
        message="Chain owner account created successfully",
        data=result,
    )


@router.post("/login", response_model=APIResponse)
async def chain_owner_login(data: ChainOwnerLoginRequest):
    """Login as chain owner"""
    result = await ChainOwnerService.login(data)
    return APIResponse(
        success=True,
        message="Login successful",
        data=result,
    )


@router.get("/outlets", response_model=APIResponse)
async def get_chain_outlets(
    current_owner: dict = Depends(get_current_chain_owner),
):
    """Get all outlets belonging to this chain"""
    result = await ChainOwnerService.get_chain_outlets(
        current_owner["chain_id"]
    )
    return APIResponse(success=True, data=result)


@router.get("/outlets/{outlet_id}/stats", response_model=APIResponse)
async def get_outlet_stats(
    outlet_id: str,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_owner: dict = Depends(get_current_chain_owner),
):
    """Get detailed stats for a specific outlet"""
    # Verify outlet belongs to this chain
    chain_outlets = await ChainOwnerService.get_chain_outlets(
        current_owner["chain_id"]
    )
    outlet_ids = [o["id"] for o in chain_outlets]
    if outlet_id not in outlet_ids:
        return APIResponse(
            success=False,
            message="Outlet does not belong to your chain",
        )

    result = await ChainOwnerService.get_outlet_stats(outlet_id, date)
    return APIResponse(success=True, data=result)


@router.get("/dashboard", response_model=APIResponse)
async def get_chain_dashboard(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_owner: dict = Depends(get_current_chain_owner),
):
    """Get aggregated dashboard data across all chain outlets"""
    result = await ChainOwnerService.get_chain_dashboard(
        current_owner["chain_id"], date
    )
    return APIResponse(success=True, data=result)
