"""
Data Transfer Objects (DTOs) for Plant API.

Pydantic v2 schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PlantCreateRequest(BaseModel):
    """DTO for creating a new plant"""
    organization_id: int = Field(gt=0, description="Organization ID (foreign key)")
    plant_code: str = Field(max_length=20, min_length=1, description="Plant code (unique within organization)")
    plant_name: str = Field(max_length=200, min_length=1, description="Plant name")
    location: Optional[str] = Field(default=None, max_length=500, description="Plant location")
    is_active: bool = Field(default=True, description="Plant active status")


class PlantUpdateRequest(BaseModel):
    """DTO for updating an existing plant (partial updates)"""
    plant_name: Optional[str] = Field(default=None, max_length=200, min_length=1)
    location: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class PlantResponse(BaseModel):
    """DTO for plant response"""
    id: int
    organization_id: int
    plant_code: str
    plant_name: str
    location: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PlantListResponse(BaseModel):
    """DTO for paginated plant list response"""
    items: list[PlantResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
