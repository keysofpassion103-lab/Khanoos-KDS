from typing import Dict
from fastapi import HTTPException, status
from datetime import timedelta
from app.database import supabase
from app.auth.utils import get_password_hash, verify_password, create_access_token
from app.config import settings
from app.schemas.admin_user import AdminUserCreate, AdminUserLogin, AdminUserUpdate
import logging

logger = logging.getLogger(__name__)


class AdminUserService:

    @staticmethod
    async def register(data: AdminUserCreate) -> Dict:
        """Register a new admin user with Supabase Auth"""

        # Check if email already exists
        existing = supabase.table("admin_users").select("id").eq(
            "email", data.email
        ).execute()

        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        try:
            logger.info(f"[ADMIN REGISTRATION] Starting registration for: {data.email}")

            # 1. Create user in Supabase Auth using admin method (bypasses RLS!)
            logger.info(f"[STEP 1/2] Creating user in Supabase Auth...")
            auth_response = supabase.auth.admin.create_user({
                "email": data.email,
                "password": data.password,
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": {
                    "full_name": data.full_name,
                    "phone": data.phone,
                    "user_type": "admin"
                }
            })

            if not auth_response.user:
                logger.error(f"[FAILED] Could not create user in Supabase Auth")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create auth user"
                )

            user_id = auth_response.user.id
            logger.info(f"✅ [SUPABASE AUTH] User created with ID: {user_id}")
            logger.info(f"   → User visible in Supabase Dashboard → Authentication → Users")

            # 2. Create entry in admin_users table with SAME ID
            logger.info(f"[STEP 2/2] Creating admin profile in admin_users table with same ID...")
            insert_data = {
                "id": user_id,  # Use SAME ID as Supabase Auth!
                "email": data.email,
                "password_hash": get_password_hash(data.password),  # Keep for backup
                "full_name": data.full_name,
                "phone": data.phone
            }

            response = supabase.table("admin_users").insert(insert_data).execute()

            if not response.data:
                # Rollback: delete auth user if profile creation fails
                logger.error(f"[FAILED] Could not create admin profile in database")
                logger.info(f"[ROLLBACK] Deleting Supabase Auth user...")
                try:
                    supabase.auth.admin.delete_user(user_id)
                    logger.info(f"[ROLLBACK] Auth user deleted successfully")
                except Exception as rollback_error:
                    logger.error(f"[ROLLBACK FAILED] {rollback_error}")

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create admin user profile"
                )

            admin = response.data[0]
            logger.info(f"✅ [DATABASE] Admin profile created with ID: {admin['id']}")
            logger.info(f"   → Saved in admin_users table")
            logger.info(f"   → Using SAME ID as Supabase Auth: {user_id}")
            logger.info(f"")
            logger.info(f"🎉 [SUCCESS] Admin registration complete!")
            logger.info(f"   📧 Email: {data.email}")
            logger.info(f"   🆔 User ID: {user_id} (same in both places)")
            logger.info(f"   ✅ Saved in BOTH Supabase Auth AND admin_users table")

            return {
                "id": admin["id"],
                "email": admin["email"],
                "full_name": admin["full_name"],
                "phone": admin.get("phone"),
                "created_at": admin["created_at"],
                "message": "✅ Admin registered successfully! Saved in BOTH Supabase Auth AND admin_users table."
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )

    @staticmethod
    async def login(data: AdminUserLogin) -> Dict:
        """Login admin user using Supabase Auth"""

        try:
            # 1. Sign in with Supabase Auth
            auth_response = supabase.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password
            })

            if not auth_response.user or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            # 2. Get admin profile from admin_users table (using SAME ID)
            admin_response = supabase.table("admin_users").select("*").eq(
                "id", auth_response.user.id  # Use same ID!
            ).execute()

            if not admin_response.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not an admin"
                )

            admin = admin_response.data[0]

            return {
                "admin": {
                    "id": admin["id"],
                    "email": admin["email"],
                    "full_name": admin["full_name"],
                    "phone": admin.get("phone"),
                    "created_at": admin["created_at"]
                },
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "token_type": "bearer"
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )

    @staticmethod
    async def get_profile(admin_id: str) -> Dict:
        """Get admin user profile"""

        response = supabase.table("admin_users").select(
            "id, email, full_name, phone, created_at"
        ).eq("id", admin_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin user not found"
            )

        return response.data[0]

    @staticmethod
    async def update(admin_id: str, data: AdminUserUpdate) -> Dict:
        """Update admin user profile"""

        update_data = data.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        response = supabase.table("admin_users").update(
            update_data
        ).eq("id", admin_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin user not found"
            )

        admin = response.data[0]
        return {
            "id": admin["id"],
            "email": admin["email"],
            "full_name": admin["full_name"],
            "phone": admin.get("phone"),
            "created_at": admin["created_at"]
        }

    @staticmethod
    async def change_password(admin_id: str, old_password: str, new_password: str) -> Dict:
        """Change admin user password in Supabase Auth"""

        try:
            # Fetch admin to get email
            response = supabase.table("admin_users").select("email").eq(
                "id", admin_id
            ).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin user not found"
                )

            admin_email = response.data[0]["email"]

            # Verify old password by attempting to sign in
            try:
                supabase.auth.sign_in_with_password({
                    "email": admin_email,
                    "password": old_password
                })
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )

            # Update password in Supabase Auth
            supabase.auth.admin.update_user_by_id(
                admin_id,
                {"password": new_password}
            )

            # Also update backup password hash in admin_users table
            new_hash = get_password_hash(new_password)
            supabase.table("admin_users").update(
                {"password_hash": new_hash}
            ).eq("id", admin_id).execute()

            logger.info(f"✅ Password changed for admin: {admin_email}")
            logger.info(f"   → Updated in BOTH Supabase Auth AND admin_users table")

            return {"message": "Password changed successfully"}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password change failed: {str(e)}"
            )
