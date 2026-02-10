"""
Admin User Service V2 - Supabase Auth Integration
This version uses Supabase Auth for authentication
Old version (admin_user_service.py) is kept as backup
"""
from typing import Dict
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.admin_user import AdminUserCreate, AdminUserLogin, AdminUserUpdate
import logging

logger = logging.getLogger(__name__)


class AdminUserServiceV2:
    """Admin user service using Supabase Auth"""

    @staticmethod
    async def register(data: AdminUserCreate) -> Dict:
        """Register a new admin user using Supabase Auth"""

        try:
            # 1. Check if email already exists in admin_users table
            existing = supabase.table("admin_users").select("id").eq(
                "email", data.email
            ).execute()

            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # 2. Create user in Supabase Auth
            logger.info(f"Creating Supabase Auth user for: {data.email}")

            auth_response = supabase.auth.sign_up({
                "email": data.email,
                "password": data.password,
                "options": {
                    "data": {
                        "full_name": data.full_name,
                        "phone": data.phone,
                        "user_type": "admin"
                    }
                }
            })

            if not auth_response.user:
                logger.error(f"Failed to create Supabase Auth user for: {data.email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create authentication user"
                )

            logger.info(f"Supabase Auth user created: {auth_response.user.id}")

            # 3. Create entry in admin_users table
            admin_data = {
                "id": auth_response.user.id,
                "email": data.email,
                "full_name": data.full_name,
                "phone": data.phone,
                "password_hash": None  # Not used with Supabase Auth
            }

            response = supabase.table("admin_users").insert(admin_data).execute()

            if not response.data:
                # Rollback: Try to delete auth user
                try:
                    supabase.auth.admin.delete_user(auth_response.user.id)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create admin profile"
                )

            admin = response.data[0]
            logger.info(f"Admin profile created: {admin['id']}")

            return {
                "admin": {
                    "id": admin["id"],
                    "email": admin["email"],
                    "full_name": admin["full_name"],
                    "phone": admin.get("phone"),
                    "created_at": admin["created_at"]
                },
                "session": {
                    "access_token": auth_response.session.access_token if auth_response.session else None,
                    "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
                    "expires_at": auth_response.session.expires_at if auth_response.session else None,
                    "token_type": "bearer"
                } if auth_response.session else None,
                "message": "Admin registered successfully. Check email for verification link."
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
            # 1. Sign in with Supabase Auth
            logger.info(f"Attempting Supabase Auth login for: {data.email}")

            auth_response = supabase.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password
            })

            if not auth_response.user or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            logger.info(f"Supabase Auth login successful: {auth_response.user.id}")

            # 2. Get admin profile from admin_users table
            admin_response = supabase.table("admin_users").select("*").eq(
                "id", str(auth_response.user.id)
            ).execute()

            if not admin_response.data:
                logger.warning(f"User {data.email} authenticated but not found in admin_users table")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not an admin"
                )

            admin = admin_response.data[0]
            logger.info(f"Admin profile retrieved: {admin['id']}")

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
                "expires_at": auth_response.session.expires_at,
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
        """Get admin user profile by ID"""

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

        return response.data[0]

    @staticmethod
    async def change_password(admin_id: str, new_password: str) -> Dict:
        """Change admin user password using Supabase Auth"""

        try:
            # Verify admin exists
            admin_response = supabase.table("admin_users").select("id").eq(
                "id", admin_id
            ).execute()

            if not admin_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin user not found"
                )

            # Update password in Supabase Auth
            # Note: This requires admin privileges or the user's current session
            supabase.auth.update_user({
                "password": new_password
            })

            return {"message": "Password changed successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password change error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password change failed: {str(e)}"
            )

    @staticmethod
    async def request_password_reset(email: str) -> Dict:
        """Request password reset email from Supabase Auth"""

        try:
            # Check if admin exists
            admin_response = supabase.table("admin_users").select("id").eq(
                "email", email
            ).execute()

            if not admin_response.data:
                # Don't reveal if email exists or not (security)
                return {"message": "If the email exists, a password reset link has been sent"}

            # Send password reset email via Supabase Auth
            supabase.auth.reset_password_for_email(email)

            return {"message": "Password reset email sent successfully"}

        except Exception as e:
            logger.error(f"Password reset request error: {str(e)}", exc_info=True)
            # Don't reveal errors to prevent email enumeration
            return {"message": "If the email exists, a password reset link has been sent"}
