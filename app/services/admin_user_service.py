from typing import Dict
from fastapi import HTTPException, status
from app.database import get_fresh_supabase_client
from app.auth.utils import get_password_hash
from app.schemas.admin_user import AdminUserCreate, AdminUserLogin, AdminUserUpdate
import logging

logger = logging.getLogger(__name__)


class AdminUserService:

    @staticmethod
    async def register(data: AdminUserCreate) -> Dict:
        """Register a new admin user in BOTH Supabase Auth AND admin_users table"""

        # Fresh client for ALL operations - guarantees service_role context
        db = get_fresh_supabase_client()

        # Check if email already exists
        existing = db.table("admin_users").select("id").eq(
            "email", data.email
        ).execute()

        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        try:
            logger.info(f"[ADMIN REGISTER] Starting for: {data.email}")

            # STEP 1: Create user in Supabase Auth (visible in Dashboard > Authentication)
            auth_client = get_fresh_supabase_client()
            auth_response = auth_client.auth.admin.create_user({
                "email": data.email,
                "password": data.password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": data.full_name,
                    "phone": data.phone,
                    "user_type": "admin"
                }
            })

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create auth user"
                )

            user_id = str(auth_response.user.id)
            logger.info(f"[AUTH] Created in Supabase Auth: {user_id}")

            # STEP 2: Create in admin_users table with SAME ID
            db2 = get_fresh_supabase_client()
            insert_data = {
                "id": user_id,
                "email": data.email,
                "password_hash": get_password_hash(data.password),
                "full_name": data.full_name,
                "phone": data.phone
            }

            response = db2.table("admin_users").insert(insert_data).execute()

            if not response.data:
                # Rollback: delete auth user
                logger.error(f"[FAILED] DB insert failed, rolling back auth user")
                try:
                    rollback_client = get_fresh_supabase_client()
                    rollback_client.auth.admin.delete_user(user_id)
                except Exception as e:
                    logger.error(f"[ROLLBACK FAILED] {e}")

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create admin user profile"
                )

            admin = response.data[0]
            logger.info(f"[SUCCESS] Admin registered: {data.email} (ID: {user_id})")

            return {
                "id": admin["id"],
                "email": admin["email"],
                "full_name": admin["full_name"],
                "phone": admin.get("phone"),
                "created_at": admin["created_at"],
                "message": "Admin registered successfully"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )

    @staticmethod
    async def login(data: AdminUserLogin) -> Dict:
        """Login admin user using Supabase Auth"""

        try:
            # Sign in with fresh client (never touches global state)
            auth_client = get_fresh_supabase_client()
            auth_response = auth_client.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password
            })

            if not auth_response.user or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            # Get admin profile with fresh client
            db = get_fresh_supabase_client()
            admin_response = db.table("admin_users").select("*").eq(
                "id", str(auth_response.user.id)
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
            logger.error(f"Login error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )

    @staticmethod
    async def get_profile(admin_id: str) -> Dict:
        """Get admin user profile"""
        db = get_fresh_supabase_client()
        response = db.table("admin_users").select(
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

        db = get_fresh_supabase_client()
        response = db.table("admin_users").update(
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
            # Fetch admin email
            db = get_fresh_supabase_client()
            response = db.table("admin_users").select("email").eq(
                "id", admin_id
            ).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin user not found"
                )

            admin_email = response.data[0]["email"]

            # Verify old password with fresh client
            try:
                verify_client = get_fresh_supabase_client()
                verify_client.auth.sign_in_with_password({
                    "email": admin_email,
                    "password": old_password
                })
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )

            # Update in Supabase Auth
            admin_client = get_fresh_supabase_client()
            admin_client.auth.admin.update_user_by_id(
                admin_id,
                {"password": new_password}
            )

            # Update backup hash in DB
            db2 = get_fresh_supabase_client()
            db2.table("admin_users").update(
                {"password_hash": get_password_hash(new_password)}
            ).eq("id", admin_id).execute()

            logger.info(f"Password changed for admin: {admin_email}")
            return {"message": "Password changed successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password change error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password change failed: {str(e)}"
            )
