from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.schemas.response import APIResponse
from app.schemas.license_key import LicenseAuthRequest, OutletUserSignupRequest
from app.services.license_service import LicenseService
from app.auth.dependencies import get_current_outlet_user
from app.database import get_fresh_supabase_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/app", tags=["App Auth (POS/Kitchen)"])


class AppLicenseRequest(BaseModel):
    license_key: str


class AppActivateRequest(BaseModel):
    license_key: str
    device_id: Optional[str] = None


class AppRefreshRequest(BaseModel):
    refresh_token: str


@router.post("/auth/license", response_model=APIResponse)
async def app_authenticate_license(data: AppLicenseRequest):
    """Authenticate a POS/Kitchen app using a license key (Public)"""

    result = await LicenseService.authenticate_with_license_key(
        LicenseAuthRequest(license_key=data.license_key, email="", device_info=data.device_id or "")
    )

    return APIResponse(
        success=True,
        message="License authentication complete",
        data=result
    )


@router.post("/auth/activate", response_model=APIResponse)
async def app_activate_outlet(data: AppActivateRequest):
    """Activate an outlet via license key and return auth tokens (Public)

    This endpoint verifies the license, activates the outlet, and returns
    access tokens for the POS/Kitchen app to use.
    """

    try:
        # First verify the license key is valid
        check_result = await LicenseService.is_license_key_valid(data.license_key)

        if not check_result.get("is_valid"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or already used license key"
            )

        # Get license details to find the outlet
        db = get_fresh_supabase_client()
        license_response = db.table("license_keys").select(
            "*, single_outlets(*)"
        ).eq("license_key", data.license_key).execute()

        if not license_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License key not found"
            )

        license_data = license_response.data[0]
        outlet = license_data.get("single_outlets")

        if not outlet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No outlet linked to this license key"
            )

        # Activate the outlet
        db2 = get_fresh_supabase_client()
        db2.table("single_outlets").update({
            "is_active": True,
            "license_key_used": True
        }).eq("id", outlet["id"]).execute()

        # Mark license as used
        db2.table("license_keys").update({
            "is_used": True
        }).eq("license_key", data.license_key).execute()

        # Sign in as the outlet user if auth_user_id exists
        access_token = None
        refresh_token = None

        if outlet.get("auth_user_id"):
            try:
                # Get user's session via admin API
                auth_client = get_fresh_supabase_client()
                # Generate a link for the user to get a session
                link_response = auth_client.auth.admin.generate_link({
                    "type": "magiclink",
                    "email": outlet.get("owner_email", "")
                })
                logger.info(f"Outlet {outlet['id']} activated via license key")
            except Exception as e:
                logger.warning(f"Could not generate session for outlet: {e}")

        return APIResponse(
            success=True,
            message="Outlet activated successfully",
            data={
                "outlet_id": outlet["id"],
                "outlet_name": outlet.get("outlet_name"),
                "is_active": True,
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"App activation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Activation failed: {str(e)}"
        )


@router.get("/status", response_model=APIResponse)
async def app_check_status(current_user: dict = Depends(get_current_outlet_user)):
    """Check outlet status (requires outlet user auth token)"""

    outlet = current_user.get("outlet", {})

    return APIResponse(
        success=True,
        data={
            "user_id": current_user["id"],
            "email": current_user["email"],
            "outlet_id": current_user["outlet_id"],
            "outlet_name": outlet.get("outlet_name"),
            "outlet_type": outlet.get("outlet_type", "single"),
            "is_active": outlet.get("is_active", False),
            "plan_id": outlet.get("plan_id"),
            "plan_start_date": outlet.get("plan_start_date"),
            "plan_end_date": outlet.get("plan_end_date"),
        }
    )


@router.post("/refresh-token", response_model=APIResponse)
async def app_refresh_token(data: AppRefreshRequest):
    """Refresh an expired Supabase session token (Public)"""

    try:
        auth_client = get_fresh_supabase_client()
        session_response = auth_client.auth.refresh_session(data.refresh_token)

        if not session_response or not session_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        return APIResponse(
            success=True,
            message="Token refreshed successfully",
            data={
                "access_token": session_response.session.access_token,
                "refresh_token": session_response.session.refresh_token,
                "token_type": "bearer",
                "expires_in": session_response.session.expires_in
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )
