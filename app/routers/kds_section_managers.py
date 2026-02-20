"""
Section Manager endpoints:
- CRUD for section managers (outlet owner only)
- Section-scoped data fetching (auto-scoped by JWT section_id)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.section_manager import SectionManagerCreate, SectionManagerUpdate
from app.services.section_manager_service import SectionManagerService
from app.services.kds_order_service import KDSOrderService
from app.services.kds_kot_service import KDSKotService
from app.services.section_table_service import SectionTableService
from app.auth.dependencies import get_current_outlet_user

router = APIRouter(prefix="/kds", tags=["KDS Section Managers"])


def _require_owner(current_user: dict):
    """Raise 403 if user is not an outlet owner."""
    if current_user.get("user_type") == "section_manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Section managers cannot access this endpoint"
        )


# ── CRUD (outlet owner only) ────────────────────────────────────────────────

@router.get("/section-managers")
async def get_section_managers(current_user: dict = Depends(get_current_outlet_user)):
    """Get all section managers for the outlet."""
    _require_owner(current_user)
    result = await SectionManagerService.get_section_managers(current_user["outlet_id"])
    return {"success": True, "data": result}


@router.post("/section-managers", status_code=status.HTTP_201_CREATED)
async def create_section_manager(
    data: SectionManagerCreate,
    current_user: dict = Depends(get_current_outlet_user),
):
    """Create a new section manager."""
    _require_owner(current_user)
    result = await SectionManagerService.create_section_manager(
        current_user["outlet_id"], data
    )
    return {"success": True, "message": "Section manager created", "data": result}


@router.put("/section-managers/{manager_id}")
async def update_section_manager(
    manager_id: str,
    data: SectionManagerUpdate,
    current_user: dict = Depends(get_current_outlet_user),
):
    """Update a section manager."""
    _require_owner(current_user)
    result = await SectionManagerService.update_section_manager(
        manager_id, current_user["outlet_id"], data
    )
    return {"success": True, "message": "Section manager updated", "data": result}


@router.delete("/section-managers/{manager_id}")
async def delete_section_manager(
    manager_id: str,
    current_user: dict = Depends(get_current_outlet_user),
):
    """Delete a section manager."""
    _require_owner(current_user)
    await SectionManagerService.delete_section_manager(
        manager_id, current_user["outlet_id"]
    )
    return {"success": True, "message": "Section manager deleted"}


# ── Section-scoped data endpoints ────────────────────────────────────────────

@router.get("/section-data/tables")
async def get_section_tables(current_user: dict = Depends(get_current_outlet_user)):
    """Get tables — scoped to section for section managers, all for owners."""
    section_id = current_user.get("section_id")
    if section_id:
        result = await SectionManagerService.get_tables_by_section(
            current_user["outlet_id"], section_id
        )
    else:
        result = await SectionTableService.get_tables(current_user["outlet_id"])
    return {"success": True, "data": result}


@router.get("/section-data/orders")
async def get_section_orders(current_user: dict = Depends(get_current_outlet_user)):
    """Get orders — scoped to section for section managers, all for owners."""
    section_id = current_user.get("section_id")
    if section_id:
        result = await SectionManagerService.get_orders_by_section(
            current_user["outlet_id"], section_id
        )
    else:
        result = await KDSOrderService.get_today_orders(current_user["outlet_id"])
    return {"success": True, "data": result}


@router.get("/section-data/kots")
async def get_section_kots(current_user: dict = Depends(get_current_outlet_user)):
    """Get active KOTs — scoped to section for section managers, all for owners."""
    section_id = current_user.get("section_id")
    if section_id:
        result = await SectionManagerService.get_kots_by_section(
            current_user["outlet_id"], section_id
        )
    else:
        result = await KDSKotService.get_today_kots(current_user["outlet_id"])
    return {"success": True, "data": result}


@router.get("/section-data/kots/served")
async def get_section_served_kots(current_user: dict = Depends(get_current_outlet_user)):
    """Get served KOTs — scoped to section for section managers, all for owners."""
    section_id = current_user.get("section_id")
    if section_id:
        result = await SectionManagerService.get_served_kots_by_section(
            current_user["outlet_id"], section_id
        )
    else:
        result = await KDSKotService.get_served_kots(current_user["outlet_id"])
    return {"success": True, "data": result}
