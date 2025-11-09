"""
Data Transfer Objects (DTOs) for Department API.

Pydantic v2 schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DepartmentCreateRequest(BaseModel):
    """DTO for creating a new department"""
    plant_id: int = Field(description="Plant ID (foreign key)")
    dept_code: str = Field(max_length=20, min_length=2, description="Department code (unique within plant)")
    dept_name: str = Field(max_length=200, min_length=1, description="Department name")
    description: Optional[str] = Field(default=None, description="Department description")
    is_active: bool = Field(default=True, description="Department active status")


class DepartmentUpdateRequest(BaseModel):
    """DTO for updating an existing department (partial updates)"""
    dept_name: Optional[str] = Field(default=None, max_length=200, min_length=1)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    """DTO for department response"""
    id: int
    plant_id: int
    dept_code: str
    dept_name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentListResponse(BaseModel):
    """DTO for paginated department list response"""
    items: list[DepartmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
