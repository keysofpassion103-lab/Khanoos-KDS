from typing import List, Dict
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.license_key import (
    LicenseKeyCreate,
    LicenseVerifyRequest,
    LicenseAuthRequest,
    OutletActivationRequest,
    OutletUserSignupRequest
)
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class LicenseService:

    @staticmethod
    async def create(data: LicenseKeyCreate) -> Dict:
        """Create a new license key entry"""

        insert_data = data.dict()
        insert_data["is_used"] = False

        response = supabase.table("license_keys").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create license key"
            )

        return response.data[0]

    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all license keys"""

        response = supabase.table("license_keys").select("*").execute()
        return response.data

    @staticmethod
    async def get_by_id(license_id: str) -> Dict:
        """Get license key by ID"""

        response = supabase.table("license_keys").select("*").eq(
            "id", license_id
        ).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License key not found"
            )

        return response.data[0]

    @staticmethod
    async def verify_license_for_signup(data: LicenseVerifyRequest) -> Dict:
        """Verify a license key for signup via RPC"""

        try:
            response = supabase.rpc(
                "verify_license_for_signup",
                {
                    "p_license_key": data.license_key,
                    "p_email": data.email
                }
            ).execute()

            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                return {
                    "valid": result.get("valid", False),
                    "message": result.get("message", "Verification complete"),
                    "outlet_id": result.get("outlet_id"),
                    "outlet_name": result.get("outlet_name"),
                    "owner_name": result.get("owner_name"),
                    "already_used": result.get("already_used", False)
                }
            else:
                return {
                    "valid": False,
                    "message": "Invalid license key",
                    "outlet_id": None,
                    "outlet_name": None,
                    "owner_name": None,
                    "already_used": False
                }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"License verification failed: {str(e)}"
            )

    @staticmethod
    async def authenticate_with_license_key(data: LicenseAuthRequest) -> Dict:
        """Authenticate using license key via RPC"""

        try:
            response = supabase.rpc(
                "authenticate_with_license_key",
                {
                    "p_license_key": data.license_key,
                    "p_email": data.email,
                    "p_device_info": data.device_info
                }
            ).execute()

            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                return {
                    "success": result.get("success", False),
                    "message": result.get("message", "Authentication complete"),
                    "outlet_id": result.get("outlet_id"),
                    "outlet_name": result.get("outlet_name"),
                    "is_active": result.get("is_active", False),
                    "auth_user_id": result.get("auth_user_id")
                }
            else:
                return {
                    "success": False,
                    "message": "Authentication failed",
                    "outlet_id": None,
                    "outlet_name": None,
                    "is_active": False,
                    "auth_user_id": None
                }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"License authentication failed: {str(e)}"
            )

    @staticmethod
    async def activate_outlet_after_signup(data: OutletActivationRequest) -> Dict:
        """Activate an outlet after signup via RPC"""

        try:
            response = supabase.rpc(
                "activate_outlet_after_signup",
                {
                    "p_outlet_id": data.outlet_id,
                    "p_auth_user_id": data.auth_user_id,
                    "p_license_key": data.license_key
                }
            ).execute()

            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                return result
            else:
                return {"success": False, "message": "Activation failed"}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Outlet activation failed: {str(e)}"
            )

    @staticmethod
    async def is_license_key_valid(license_key: str) -> Dict:
        """Check if a license key is valid via RPC"""

        try:
            response = supabase.rpc(
                "is_license_key_valid",
                {"p_license_key": license_key}
            ).execute()

            if response.data is not None:
                is_valid = response.data
                if isinstance(is_valid, list) and len(is_valid) > 0:
                    is_valid = is_valid[0]
                return {"is_valid": bool(is_valid), "license_key": license_key}
            else:
                return {"is_valid": False, "license_key": license_key}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"License validation failed: {str(e)}"
            )

    @staticmethod
    async def signup_outlet_user(data: OutletUserSignupRequest) -> Dict:
        """Create outlet user in Supabase Auth and activate license"""

        try:
            logger.info(f"[OUTLET SIGNUP] Starting signup for: {data.email}")

            # 1. Verify license key is valid
            logger.info(f"[STEP 1/4] Verifying license key...")
            verify_response = await LicenseService.verify_license_for_signup(
                LicenseVerifyRequest(license_key=data.license_key, email=data.email)
            )

            if not verify_response.get("valid"):
                logger.warning(f"[FAILED] Invalid license key")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=verify_response.get("message", "Invalid license key")
                )

            if verify_response.get("already_used"):
                logger.warning(f"[FAILED] License key already used")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="License key is already activated. Please login instead."
                )

            outlet_id = verify_response.get("outlet_id")
            outlet_name = verify_response.get("outlet_name")
            logger.info(f"✅ License verified for outlet: {outlet_name} ({outlet_id})")

            # 2. Create user in Supabase Auth using admin method (bypasses RLS!)
            logger.info(f"[STEP 2/4] Creating user in Supabase Auth...")
            auth_response = supabase.auth.admin.create_user({
                "email": data.email,
                "password": data.password,
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": {
                    "full_name": data.full_name,
                    "user_type": "outlet_owner",
                    "outlet_id": outlet_id
                }
            })

            if not auth_response.user:
                logger.error(f"[FAILED] Could not create user in Supabase Auth")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create outlet user account"
                )

            logger.info(f"✅ [SUPABASE AUTH] User created with ID: {auth_response.user.id}")
            logger.info(f"   → User visible in Supabase Dashboard → Authentication → Users")

            # 3. Activate outlet (link stored in auth user metadata)
            logger.info(f"[STEP 3/4] Activating outlet in single_outlets table...")
            outlet_update = supabase.table("single_outlets").update({
                "is_active": True,
                "license_key_used": True
            }).eq("id", outlet_id).execute()

            logger.info(f"✅ [DATABASE] Outlet activated in single_outlets table")
            logger.info(f"   → Outlet ID: {outlet_id}")
            logger.info(f"   → Linked via auth user metadata (outlet_id: {outlet_id})")
            logger.info(f"   → Auth User ID: {auth_response.user.id}")
            logger.info(f"   → Status: Active")

            # 4. Mark license as used
            logger.info(f"[STEP 4/4] Marking license as used...")
            supabase.table("license_keys").update({
                "is_used": True,
                "used_by": data.email,
                "used_at": datetime.now(timezone.utc).isoformat()
            }).eq("license_key", data.license_key).execute()

            logger.info(f"✅ [DATABASE] License marked as used")
            logger.info(f"")
            logger.info(f"🎉 [SUCCESS] Outlet user signup complete!")
            logger.info(f"   📧 Email: {data.email}")
            logger.info(f"   🏪 Outlet: {outlet_name}")
            logger.info(f"   🔐 Auth ID: {auth_response.user.id}")
            logger.info(f"   ✅ Saved in BOTH Supabase Auth AND single_outlets table")

            return {
                "success": True,
                "message": "✅ Outlet user created successfully! You can now login with your credentials.",
                "user": {
                    "id": auth_response.user.id,
                    "email": data.email,
                    "full_name": data.full_name
                },
                "outlet": {
                    "id": outlet_id,
                    "name": outlet_name,
                    "is_active": True
                },
                "note": "Please use the login endpoint to get your access token."
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Outlet user signup failed: {str(e)}"
            )
