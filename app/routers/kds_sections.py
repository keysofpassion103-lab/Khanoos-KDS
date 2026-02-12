from fastapi import APIRouter, Depends, status
from app.schemas.kds import (
    SectionCreate, SectionUpdate,
    TableCreate, TableUpdate, TableStatusUpdate
)
from app.schemas.response import APIResponse
from app.services.section_table_service import SectionTableService
from app.auth.dependencies import get_current_outlet_user

router = APIRouter(prefix="/kds", tags=["KDS Sections & Tables"])


# ═══════════════════════════════════════════════════════════════════════════
# SECTIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/sections", response_model=APIResponse)
async def get_sections(current_user: dict = Depends(get_current_outlet_user)):
    """Get all active sections for the current outlet"""
    result = await SectionTableService.get_sections(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/sections", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    data: SectionCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Create a new section"""
    result = await SectionTableService.create_section(current_user["outlet_id"], data)
    return APIResponse(success=True, message="Section created successfully", data=result)


@router.put("/sections/{section_id}", response_model=APIResponse)
async def update_section(
    section_id: str,
    data: SectionUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Update a section"""
    result = await SectionTableService.update_section(section_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Section updated successfully", data=result)


@router.delete("/sections/{section_id}", response_model=APIResponse)
async def delete_section(
    section_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Delete a section"""
    await SectionTableService.delete_section(section_id, current_user["outlet_id"])
    return APIResponse(success=True, message="Section deleted successfully")


# ═══════════════════════════════════════════════════════════════════════════
# TABLES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/tables", response_model=APIResponse)
async def get_tables(current_user: dict = Depends(get_current_outlet_user)):
    """Get all tables for the current outlet with section info"""
    result = await SectionTableService.get_tables(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("/tables", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_table(
    data: TableCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Create a new table"""
    result = await SectionTableService.create_table(current_user["outlet_id"], data)
    return APIResponse(success=True, message="Table created successfully", data=result)


@router.put("/tables/{table_id}", response_model=APIResponse)
async def update_table(
    table_id: str,
    data: TableUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Update a table"""
    result = await SectionTableService.update_table(table_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Table updated successfully", data=result)


@router.patch("/tables/{table_id}/status", response_model=APIResponse)
async def update_table_status(
    table_id: str,
    data: TableStatusUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Update table status"""
    result = await SectionTableService.update_table_status(table_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Table status updated", data=result)


@router.delete("/tables/{table_id}", response_model=APIResponse)
async def delete_table(
    table_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Delete a table"""
    await SectionTableService.delete_table(table_id, current_user["outlet_id"])
    return APIResponse(success=True, message="Table deleted successfully")
