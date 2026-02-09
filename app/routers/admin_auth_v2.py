"""
Admin Authentication Router V2 - Supabase Auth
New endpoints using Supabase Authentication
Old endpoints in admin_auth.py remain unchanged for safety
"""
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, Field
from app.schemas.admin_user import AdminUserCreate, AdminUserLogin, AdminUserUpdate
from app.schemas.response import APIResponse
from app.services.admin_user_service_v2 import AdminUserServiceV2
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin-auth-v2", tags=["Admin Authentication V2 (Supabase Auth)"])


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordChangeRequest(BaseModel):
    """Password change request schema (V2 - Supabase Auth)"""
    new_password: str = Field(min_length=8, max_length=100)


@router.post("/register", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def register_admin_v2(data: AdminUserCreate):
    """
    Register a new admin user using Supabase Auth

    **Features:**
    - Creates user in Supabase Auth (visible in dashboard)
    - Sends email verification link
    - Returns session token

    **Differences from V1:**
    - User appears in Supabase Dashboard → Authentication
    - Built-in email verification
    - Supabase manages password security
    """
    logger.info(f"V2 Registration attempt for: {data.email}")

    result = await AdminUserServiceV2.register(data)

    return APIResponse(
        success=True,
        message=result.get("message", "Admin registered successfully"),
        data=result
    )


@router.post("/login", response_model=APIResponse)
async def login_admin_v2(data: AdminUserLogin):
    """
    Login admin user using Supabase Auth

    **Features:**
    - Uses Supabase Auth for authentication
    - Returns Supabase session token
    - Token works with Supabase RLS policies

    **Differences from V1:**
    - Uses Supabase Auth instead of custom JWT
    - Session managed by Supabase
    - More secure and feature-rich
    """
    logger.info(f"V2 Login attempt for: {data.email}")

    result = await AdminUserServiceV2.login(data)

    return APIResponse(
        success=True,
        message="Login successful",
        data=result
    )


@router.post("/password-reset-request", response_model=APIResponse)
async def request_password_reset(data: PasswordResetRequest):
    """
    Request password reset email

    **Features:**
    - Sends password reset link to email
    - Link handled by Supabase Auth
    - Secure token-based reset

    **New Feature:** Not available in V1
    """
    logger.info(f"Password reset requested for: {data.email}")

    result = await AdminUserServiceV2.request_password_reset(data.email)

    return APIResponse(
        success=True,
        message=result.get("message"),
        data=result
    )


@router.get("/", response_model=APIResponse)
async def get_v2_info():
    """
    Get information about V2 endpoints

    Returns comparison between V1 and V2 authentication systems
    """
    return APIResponse(
        success=True,
        message="Admin Auth V2 - Supabase Auth Integration",
        data={
            "version": "2.0",
            "description": "Uses Supabase Authentication for admin users",
            "features": {
                "email_verification": True,
                "password_reset": True,
                "session_management": True,
                "visible_in_dashboard": True,
                "oauth_ready": True
            },
            "differences_from_v1": {
                "authentication": "Supabase Auth (not custom bcrypt)",
                "tokens": "Supabase session tokens (not custom JWT)",
                "password_storage": "Managed by Supabase (more secure)",
                "user_visibility": "Visible in Supabase Dashboard → Authentication"
            },
            "endpoints": {
                "register": "POST /api/v1/admin-auth-v2/register",
                "login": "POST /api/v1/admin-auth-v2/login",
                "password_reset": "POST /api/v1/admin-auth-v2/password-reset-request"
            },
            "migration_status": "Both V1 and V2 are active - test V2, then switch",
            "rollback": "V1 endpoints still available at /api/v1/admin-auth/*"
        }
    )


# Additional endpoints for future use

@router.get("/session-info", response_model=APIResponse)
async def get_session_info():
    """
    Get information about current Supabase Auth session

    Requires: Authorization header with Supabase access token
    """
    return APIResponse(
        success=True,
        message="Session info endpoint",
        data={
            "note": "This endpoint will validate and return session information",
            "implementation": "Coming soon"
        }
    )
