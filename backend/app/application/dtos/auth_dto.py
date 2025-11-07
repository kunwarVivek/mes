from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class LoginDTO(BaseModel):
    """DTO for user login"""
    email: EmailStr
    password: str


class TokenResponseDTO(BaseModel):
    """DTO for token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None


class RefreshTokenDTO(BaseModel):
    """DTO for refresh token request"""
    refresh_token: str
