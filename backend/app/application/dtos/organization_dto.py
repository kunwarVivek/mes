"""
Data Transfer Objects (DTOs) for Organization API.

Pydantic v2 schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


class OrganizationCreateRequest(BaseModel):
    """DTO for creating a new organization"""
    org_code: str = Field(max_length=20, min_length=2, description="Unique organization code (uppercase alphanumeric)")
    org_name: str = Field(max_length=200, min_length=1, description="Organization name")
    subdomain: Optional[str] = Field(default=None, max_length=100, description="Subdomain for white-label access")
    is_active: bool = Field(default=True, description="Organization active status")

    @field_validator('org_code')
    @classmethod
    def validate_org_code(cls, v: str) -> str:
        """Validate org_code format (uppercase alphanumeric)"""
        if not re.match(r'^[A-Z0-9]+$', v):
            raise ValueError('org_code must be uppercase alphanumeric only')
        return v

    @field_validator('subdomain')
    @classmethod
    def validate_subdomain(cls, v: Optional[str]) -> Optional[str]:
        """Validate subdomain format (lowercase alphanumeric with hyphens)"""
        if v is None:
            return v
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('subdomain must be lowercase alphanumeric with hyphens only')
        return v


class OrganizationUpdateRequest(BaseModel):
    """DTO for updating an existing organization (partial updates)"""
    org_name: Optional[str] = Field(default=None, max_length=200, min_length=1)
    subdomain: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None

    @field_validator('subdomain')
    @classmethod
    def validate_subdomain(cls, v: Optional[str]) -> Optional[str]:
        """Validate subdomain format (lowercase alphanumeric with hyphens)"""
        if v is None:
            return v
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('subdomain must be lowercase alphanumeric with hyphens only')
        return v


class OrganizationResponse(BaseModel):
    """DTO for organization response"""
    id: int
    org_code: str
    org_name: str
    subdomain: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    """DTO for paginated organization list response"""
    items: list[OrganizationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
