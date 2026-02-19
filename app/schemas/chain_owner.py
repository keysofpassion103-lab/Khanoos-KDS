from pydantic import BaseModel, Field
from typing import Optional


class ChainOwnerSignupRequest(BaseModel):
    """Request model for chain owner signup"""
    master_license_key: str
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)


class ChainOwnerLoginRequest(BaseModel):
    """Request model for chain owner login"""
    email: str
    password: str
