from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class LoginDTO(BaseModel):
    """DTO for user login"""
    email: EmailStr
    password: str


class TokenResponseDTO(BaseModel):
    """DTO for token response with tenant context"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None
    organization_id: Optional[int] = None
    plant_id: Optional[int] = None


class RefreshTokenDTO(BaseModel):
    """DTO for refresh token request"""
    refresh_token: str
