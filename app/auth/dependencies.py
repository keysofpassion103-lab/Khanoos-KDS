from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.auth.utils import decode_token
from app.database import supabase

security = HTTPBearer()

async def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated admin user from JWT token (admin_users table)"""
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check that token was issued for an admin_user
    if payload.get("user_type") != "admin_user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )

    admin_id: str = payload.get("sub")
    if admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Fetch admin from admin_users table
    response = supabase.table("admin_users").select("*").eq("id", admin_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found"
        )

    return response.data[0]