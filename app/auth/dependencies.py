from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.database import get_fresh_supabase_client
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
        # Validate token with Supabase Auth (fresh client to avoid state contamination)
        auth_client = get_fresh_supabase_client()
        user_response = auth_client.auth.get_user(token)

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

    # Check that user exists in admin_users table (fresh client for clean service role context)
    db = get_fresh_supabase_client()
    response = db.table("admin_users").select("*").eq("id", user_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )

    return response.data[0]


async def get_current_outlet_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current authenticated outlet user by validating Supabase session token"""

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
        # Validate token with Supabase Auth (fresh client to avoid state contamination)
        auth_client = get_fresh_supabase_client()
        user_response = auth_client.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = user_response.user
        user_id = str(user.id)

        # Extract outlet_id from user metadata
        outlet_id = user.user_metadata.get("outlet_id") if user.user_metadata else None

        if not outlet_id:
            logger.error(f"[AUTH] User {user_id} has no outlet_id in metadata")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions. Outlet access required."
            )

        logger.info(f"[AUTH] Token valid for outlet user: {user_id}, outlet: {outlet_id}")

        # Verify outlet exists and is active (fresh client for clean service role context)
        db = get_fresh_supabase_client()
        outlet_response = db.table("single_outlets").select("*").eq("id", outlet_id).execute()

        if not outlet_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Outlet not found or inactive"
            )

        outlet = outlet_response.data[0]

        if not outlet.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Outlet is not active"
            )

        # Return user info with outlet_id
        return {
            "id": user_id,
            "email": user.email,
            "outlet_id": outlet_id,
            "outlet": outlet
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUTH] Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_chain_owner(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current authenticated chain owner by validating Supabase session token"""

    auth_header = request.headers.get("Authorization", "MISSING")
    logger.info(f"[AUTH] {request.method} {request.url.path} | Authorization: {auth_header[:30] if auth_header != 'MISSING' else 'MISSING'}...")

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        auth_client = get_fresh_supabase_client()
        user_response = auth_client.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = user_response.user
        user_id = str(user.id)

        # Verify user_type is chain_owner
        user_type = user.user_metadata.get("user_type", "") if user.user_metadata else ""
        if user_type != "chain_owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a chain owner account."
            )

        chain_id = user.user_metadata.get("chain_id") if user.user_metadata else None
        if not chain_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No chain linked to this account."
            )

        logger.info(f"[AUTH] Token valid for chain owner: {user_id}, chain: {chain_id}")

        # Verify chain exists
        db = get_fresh_supabase_client()
        chain_response = db.table("chain_outlets").select("*").eq("id", chain_id).execute()

        if not chain_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chain not found"
            )

        chain = chain_response.data[0]

        return {
            "id": user_id,
            "email": user.email,
            "chain_id": chain_id,
            "chain": chain
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUTH] Chain owner token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
