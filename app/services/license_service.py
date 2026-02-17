from typing import List, Dict
from fastapi import HTTPException, status
from app.database import get_fresh_supabase_client, get_anon_supabase_client
from app.schemas.license_key import (
    LicenseKeyCreate,
    LicenseVerifyRequest,
    LicenseAuthRequest,
    OutletActivationRequest,
    OutletUserSignupRequest,
    OutletUserLoginRequest
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

        db = get_fresh_supabase_client()
        response = db.table("license_keys").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create license key"
            )

        return response.data[0]

    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all license keys"""

        db = get_fresh_supabase_client()
        response = db.table("license_keys").select("*").execute()
        return response.data

    @staticmethod
    async def get_by_id(license_id: str) -> Dict:
        """Get license key by ID"""

        db = get_fresh_supabase_client()
        response = db.table("license_keys").select("*").eq(
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
            db = get_fresh_supabase_client()
            response = db.rpc(
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
            db = get_fresh_supabase_client()
            response = db.rpc(
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
            db = get_fresh_supabase_client()
            response = db.rpc(
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
            db = get_fresh_supabase_client()
            response = db.rpc(
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

            db = get_fresh_supabase_client()

            # 1. Look up license key directly — no email-matching required
            logger.info(f"[STEP 1/4] Verifying license key...")
            lic_resp = db.table("license_keys").select(
                "id, license_key, outlet_id, is_used"
            ).eq("license_key", data.license_key).execute()

            if not lic_resp.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid license key"
                )

            license_row = lic_resp.data[0]
            outlet_id = license_row.get("outlet_id")
            already_used = license_row.get("is_used", False)

            if not outlet_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="License key is not linked to any outlet"
                )

            # 2. Get outlet details
            outlet_resp = db.table("single_outlets").select(
                "id, outlet_name, owner_name"
            ).eq("id", outlet_id).execute()

            if not outlet_resp.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Outlet not found for this license key"
                )

            outlet = outlet_resp.data[0]
            outlet_name = outlet.get("outlet_name", "")
            owner_name = outlet.get("owner_name", "")
            full_name = data.full_name or owner_name

            logger.info(f"License verified for outlet: {outlet_name} ({outlet_id}), already_used={already_used}")

            # 3. Create user in Supabase Auth
            logger.info(f"[STEP 3/4] Creating user in Supabase Auth...")
            auth_client = get_fresh_supabase_client()
            try:
                auth_response = auth_client.auth.admin.create_user({
                    "email": data.email,
                    "password": data.password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": full_name,
                        "user_type": "outlet_owner",
                        "outlet_id": outlet_id
                    }
                })
            except Exception as auth_err:
                err_msg = str(auth_err).lower()
                if "already registered" in err_msg or "already exists" in err_msg or "email address is already" in err_msg:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="An account with this email already exists. Please login instead."
                    )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create account: {str(auth_err)}"
                )

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create outlet user account"
                )

            logger.info(f"[SUPABASE AUTH] User created with ID: {auth_response.user.id}")

            fresh_client = get_fresh_supabase_client()

            if not already_used:
                # 4. Activate outlet and mark license used
                logger.info(f"[STEP 4/4] Activating outlet and marking license used...")
                fresh_client.table("single_outlets").update({
                    "is_active": True,
                    "license_key_used": True
                }).eq("id", outlet_id).execute()

                fresh_client.table("license_keys").update({
                    "is_used": True,
                    "used_by": data.email,
                    "used_at": datetime.now(timezone.utc).isoformat()
                }).eq("license_key", data.license_key).execute()

                logger.info(f"Outlet activated: {outlet_id}")
            else:
                logger.info(f"[SKIP 4] License already used, outlet already active")

            logger.info(f"[SUCCESS] Outlet user signup complete for: {data.email}")

            return {
                "success": True,
                "message": "Outlet user created successfully. You can now login with your credentials.",
                "user": {
                    "id": str(auth_response.user.id),
                    "email": data.email,
                    "full_name": full_name
                },
                "outlet": {
                    "id": outlet_id,
                    "name": outlet_name,
                    "is_active": True
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Outlet signup error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Outlet user signup failed: {str(e)}"
            )

    @staticmethod
    async def login_outlet_user(data: OutletUserLoginRequest) -> Dict:
        """Login outlet user via Supabase Auth"""

        try:
            logger.info(f"[OUTLET LOGIN] Attempting login for: {data.email}")

            # 1. Sign in with Supabase Auth using the anon key client
            # sign_in_with_password must NOT use the service role key
            anon_client = get_anon_supabase_client()
            auth_response = anon_client.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password
            })

            if not auth_response.user or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            user = auth_response.user
            user_id = str(user.id)

            # 2. Extract outlet_id from user metadata
            outlet_id = user.user_metadata.get("outlet_id") if user.user_metadata else None

            if not outlet_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This account is not linked to any outlet. Please contact admin."
                )

            # 3. Verify outlet exists and is active (fresh client after auth operation)
            db = get_fresh_supabase_client()
            outlet_response = db.table("single_outlets").select("*").eq(
                "id", outlet_id
            ).execute()

            if not outlet_response.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Outlet not found"
                )

            outlet = outlet_response.data[0]

            if not outlet.get("is_active", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Outlet is not active. Please contact admin."
                )

            # Check plan expiry
            if outlet.get("plan_end_date"):
                from datetime import datetime as dt
                plan_end = dt.fromisoformat(outlet["plan_end_date"].replace("Z", "+00:00"))
                if plan_end < dt.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Your plan has expired. Please contact admin for renewal."
                    )

            logger.info(f"[SUCCESS] Outlet login for: {data.email}, outlet: {outlet_id}")

            return {
                "user": {
                    "id": user_id,
                    "email": user.email,
                    "full_name": user.user_metadata.get("full_name", ""),
                    "user_type": user.user_metadata.get("user_type", "outlet_owner")
                },
                "outlet": {
                    "id": outlet["id"],
                    "outlet_name": outlet["outlet_name"],
                    "outlet_type": outlet.get("outlet_type", "single"),
                    "is_active": outlet["is_active"],
                    "plan_end_date": outlet.get("plan_end_date")
                },
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "token_type": "bearer"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Outlet login error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )
