from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class CreateUserDTO(BaseModel):
    """DTO for creating a new user"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    organization_id: Optional[int] = None
    plant_id: Optional[int] = None
    is_active: bool = True
    is_superuser: bool = False


class UpdateUserDTO(BaseModel):
    """DTO for updating an existing user"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    organization_id: Optional[int] = None
    plant_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponseDTO(BaseModel):
    """DTO for user response"""
    id: int
    email: str
    username: str
    organization_id: Optional[int] = None
    plant_id: Optional[int] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
