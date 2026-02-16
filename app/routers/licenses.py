from fastapi import APIRouter, Depends, status
from app.schemas.license_key import (
    LicenseKeyCreate, LicenseVerifyRequest, LicenseAuthRequest,
    OutletActivationRequest, OutletUserSignupRequest, OutletUserLoginRequest
)
from app.schemas.response import APIResponse
from app.services.license_service import LicenseService
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/licenses", tags=["Licenses"])


# --- Public endpoints (no auth required) ---

@router.post("/verify", response_model=APIResponse)
async def verify_license(data: LicenseVerifyRequest):
    """Verify a license key for signup (Public)"""

    result = await LicenseService.verify_license_for_signup(data)

    return APIResponse(
        success=True,
        message="License verification complete",
        data=result
    )


@router.post("/authenticate", response_model=APIResponse)
async def authenticate_license(data: LicenseAuthRequest):
    """Authenticate using a license key (Public)"""

    result = await LicenseService.authenticate_with_license_key(data)

    return APIResponse(
        success=True,
        message="Authentication complete",
        data=result
    )


@router.post("/activate", response_model=APIResponse)
async def activate_outlet(data: OutletActivationRequest):
    """Activate an outlet after signup (Public)"""

    result = await LicenseService.activate_outlet_after_signup(data)

    return APIResponse(
        success=True,
        message="Activation complete",
        data=result
    )


@router.get("/check/{license_key}", response_model=APIResponse)
async def check_license_key(license_key: str):
    """Check if a license key is valid (Public)"""

    result = await LicenseService.is_license_key_valid(license_key)

    return APIResponse(
        success=True,
        data=result
    )


@router.post("/outlet-signup", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def outlet_user_signup(data: OutletUserSignupRequest):
    """
    Outlet user signup with license key (Public)

    Creates user in Supabase Auth and activates license.
    User will appear in Supabase Dashboard → Authentication → Users
    """

    result = await LicenseService.signup_outlet_user(data)

    return APIResponse(
        success=True,
        message=result.get("message", "Outlet user registered successfully"),
        data=result
    )


@router.post("/outlet-login", response_model=APIResponse)
async def outlet_user_login(data: OutletUserLoginRequest):
    """
    Login outlet user with email and password (Public)

    After first-time signup with license key, outlet users login
    with just email and password. Returns access token and outlet info.
    """

    result = await LicenseService.login_outlet_user(data)

    return APIResponse(
        success=True,
        message="Login successful",
        data=result
    )


# --- Admin endpoints (auth required) ---

@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_license_key(
    data: LicenseKeyCreate,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Create a new license key (Admin only)"""

    result = await LicenseService.create(data)

    return APIResponse(
        success=True,
        message="License key created successfully",
        data=result
    )


@router.get("", response_model=APIResponse)
async def get_all_license_keys(current_admin: dict = Depends(get_current_admin_user)):
    """Get all license keys (Admin only)"""

    result = await LicenseService.get_all()

    return APIResponse(
        success=True,
        data=result
    )


@router.get("/{license_id}", response_model=APIResponse)
async def get_license_key(
    license_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get license key by ID (Admin only)"""

    result = await LicenseService.get_by_id(license_id)

    return APIResponse(
        success=True,
        data=result
    )
