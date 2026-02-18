from fastapi import APIRouter, Depends, status
import logging
from app.schemas.license_key import (
    LicenseKeyCreate, LicenseVerifyRequest, LicenseAuthRequest,
    OutletActivationRequest, OutletUserLoginRequest,
    OutletAuthRequest,
)

logger = logging.getLogger(__name__)
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
async def outlet_user_signup(data: OutletAuthRequest):
    """
    Outlet user signup with license key (Public)

    Unified auth flow — handles both new registrations
    and cases where the account already exists (returns token either way).
    """
    result = await LicenseService.outlet_authenticate(data)

    return APIResponse(
        success=True,
        message="Outlet user registered successfully",
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


@router.post("/outlet-auth", response_model=APIResponse)
async def outlet_auth(data: OutletAuthRequest):
    """
    Unified outlet authentication (Public)

    Single endpoint for both first-time registration and returning login.
    Provide license_key + email + password every time.
    - First use: creates account, activates outlet, returns token
    - Returning use: logs in directly, returns token
    """

    result = await LicenseService.outlet_authenticate(data)

    return APIResponse(
        success=True,
        message="Authentication successful",
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
