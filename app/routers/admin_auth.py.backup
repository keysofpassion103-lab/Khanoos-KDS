from fastapi import APIRouter, Depends, status
from app.schemas.admin_user import (
    AdminUserCreate, AdminUserLogin, AdminUserUpdate, AdminChangePasswordRequest
)
from app.schemas.response import APIResponse
from app.services.admin_user_service import AdminUserService
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin-auth", tags=["Admin Authentication"])


@router.post("/register", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def register_admin(data: AdminUserCreate):
    """Register a new admin user"""

    result = await AdminUserService.register(data)

    return APIResponse(
        success=True,
        message="Admin registered successfully",
        data=result
    )


@router.post("/login", response_model=APIResponse)
async def login_admin(data: AdminUserLogin):
    """Login admin user and get access token"""

    result = await AdminUserService.login(data)

    return APIResponse(
        success=True,
        message="Login successful",
        data=result
    )


@router.get("/me", response_model=APIResponse)
async def get_admin_profile(current_admin: dict = Depends(get_current_admin_user)):
    """Get current admin user profile"""

    result = await AdminUserService.get_profile(current_admin["id"])

    return APIResponse(
        success=True,
        data=result
    )


@router.put("/me", response_model=APIResponse)
async def update_admin_profile(
    data: AdminUserUpdate,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Update current admin user profile"""

    result = await AdminUserService.update(current_admin["id"], data)

    return APIResponse(
        success=True,
        message="Profile updated successfully",
        data=result
    )


@router.post("/change-password", response_model=APIResponse)
async def change_admin_password(
    data: AdminChangePasswordRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Change admin user password"""

    result = await AdminUserService.change_password(
        current_admin["id"],
        data.old_password,
        data.new_password
    )

    return APIResponse(
        success=True,
        message="Password changed successfully",
        data=result
    )
