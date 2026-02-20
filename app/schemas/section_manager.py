"""
Pydantic schemas for Section Manager CRUD operations.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SectionManagerCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    section_id: str


class SectionManagerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    section_id: Optional[str] = None
    is_active: Optional[bool] = None
