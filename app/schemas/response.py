from pydantic import BaseModel
from typing import Optional, Any

class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: dict