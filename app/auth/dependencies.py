from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.database import supabase
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

async def get_current_admin_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current authenticated admin user by validating Supabase session token"""

    # Log for debugging
    auth_header = request.headers.get("Authorization", "MISSING")
    logger.info(f"[AUTH] {request.method} {request.url.path} | Authorization: {auth_header[:30] if auth_header != 'MISSING' else 'MISSING'}...")

    if credentials is None:
        logger.warning(f"[AUTH] No Bearer token found in request to {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Validate token with Supabase Auth
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = str(user_response.user.id)
        logger.info(f"[AUTH] Token valid for user: {user_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUTH] Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check that user exists in admin_users table
    response = supabase.table("admin_users").select("*").eq("id", user_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )

    return response.data[0]
