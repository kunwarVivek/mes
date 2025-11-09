"""
Project DTOs - Data Transfer Objects for Project API.

Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from app.domain.entities.project import ProjectStatus


class ProjectCreateRequest(BaseModel):
    """Request schema for creating a new project"""
    organization_id: int = Field(..., gt=0)
    plant_id: int = Field(..., gt=0)
    project_code: str = Field(..., max_length=50, pattern="^[A-Z0-9_-]+$")
    project_name: str = Field(..., max_length=200)
    description: Optional[str] = None
    bom_id: Optional[int] = Field(None, gt=0)
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    priority: int = Field(default=0, ge=0)

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdateRequest(BaseModel):
    """Request schema for updating an existing project"""
    project_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    bom_id: Optional[int] = Field(None, gt=0)
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    """Response schema for project data"""
    id: int
    organization_id: int
    plant_id: int
    project_code: str
    project_name: str
    description: Optional[str]
    bom_id: Optional[int]
    planned_start_date: Optional[date]
    planned_end_date: Optional[date]
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]
    status: ProjectStatus
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Response schema for paginated project list"""
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
