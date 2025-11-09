"""
Data Transfer Objects (DTOs) for BOM (Bill of Materials) API.

Pydantic v2 schemas for request/response validation.
Phase 3: Production Planning Module - BOM Component
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.bom import BOMType


class BOMHeaderCreateRequest(BaseModel):
    """DTO for creating a new BOM header"""
    organization_id: int = Field(gt=0, description="Organization ID")
    plant_id: int = Field(gt=0, description="Plant ID")
    bom_number: str = Field(max_length=50, description="BOM number (unique)")
    material_id: int = Field(gt=0, description="Material ID (finished good)")
    bom_version: int = Field(default=1, ge=1, description="BOM version (defaults to 1)")
    bom_name: str = Field(max_length=200, min_length=1, description="BOM name")
    bom_type: BOMType = Field(description="BOM type (PRODUCTION, ENGINEERING, PLANNING)")
    base_quantity: float = Field(gt=0, description="Base quantity for BOM (must be positive)")
    unit_of_measure_id: int = Field(gt=0, description="Unit of measure ID")
    effective_start_date: Optional[date] = Field(default=None, description="Effective start date")
    effective_end_date: Optional[date] = Field(default=None, description="Effective end date")
    is_active: bool = Field(default=True, description="Active status")
    created_by_user_id: int = Field(gt=0, description="User ID who created this BOM")

    @field_validator('base_quantity')
    @classmethod
    def validate_base_quantity(cls, v: float) -> float:
        """Validate base quantity is positive"""
        if v <= 0:
            raise ValueError('base_quantity must be positive')
        return v

    @field_validator('bom_version')
    @classmethod
    def validate_bom_version(cls, v: int) -> int:
        """Validate BOM version is at least 1"""
        if v < 1:
            raise ValueError('bom_version must be at least 1')
        return v


class BOMHeaderUpdateRequest(BaseModel):
    """DTO for updating an existing BOM header (partial updates)"""
    bom_name: Optional[str] = Field(default=None, max_length=200, min_length=1)
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    is_active: Optional[bool] = None


class BOMLineCreateRequest(BaseModel):
    """DTO for creating a BOM line (component in BOM)"""
    bom_header_id: int = Field(gt=0, description="BOM header ID")
    line_number: int = Field(gt=0, description="Line number (sequence within BOM)")
    component_material_id: int = Field(gt=0, description="Component material ID")
    quantity: float = Field(gt=0, description="Component quantity required")
    unit_of_measure_id: int = Field(gt=0, description="Unit of measure ID")
    scrap_factor: float = Field(default=0.0, ge=0, le=100, description="Scrap factor percentage (0-100)")
    operation_number: Optional[int] = Field(default=None, gt=0, description="Operation number where component is consumed")
    is_phantom: bool = Field(default=False, description="Phantom BOM flag (exploded during planning)")
    backflush: bool = Field(default=False, description="Backflush flag (auto-consume on completion)")

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        """Validate quantity is positive"""
        if v <= 0:
            raise ValueError('quantity must be positive')
        return v

    @field_validator('line_number')
    @classmethod
    def validate_line_number(cls, v: int) -> int:
        """Validate line number is positive"""
        if v <= 0:
            raise ValueError('line_number must be positive')
        return v

    @field_validator('scrap_factor')
    @classmethod
    def validate_scrap_factor(cls, v: float) -> float:
        """Validate scrap factor is in 0-100 range"""
        if v < 0 or v > 100:
            raise ValueError('scrap_factor must be between 0 and 100')
        return v


class BOMLineUpdateRequest(BaseModel):
    """DTO for updating an existing BOM line (partial updates)"""
    quantity: Optional[float] = Field(default=None, gt=0, description="Component quantity required")
    scrap_factor: Optional[float] = Field(default=None, ge=0, le=100, description="Scrap factor percentage (0-100)")
    operation_number: Optional[int] = Field(default=None, gt=0, description="Operation number where component is consumed")
    is_phantom: Optional[bool] = Field(default=None, description="Phantom BOM flag")
    backflush: Optional[bool] = Field(default=None, description="Backflush flag")

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: Optional[float]) -> Optional[float]:
        """Validate quantity is positive"""
        if v is not None and v <= 0:
            raise ValueError('quantity must be positive')
        return v

    @field_validator('scrap_factor')
    @classmethod
    def validate_scrap_factor(cls, v: Optional[float]) -> Optional[float]:
        """Validate scrap factor is in 0-100 range"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('scrap_factor must be between 0 and 100')
        return v


class BOMLineResponse(BaseModel):
    """DTO for BOM line response"""
    id: int
    bom_header_id: int
    line_number: int
    component_material_id: int
    quantity: float
    unit_of_measure_id: int
    scrap_factor: float
    operation_number: Optional[int] = None
    is_phantom: bool
    backflush: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BOMHeaderResponse(BaseModel):
    """DTO for BOM header response"""
    id: int
    organization_id: int
    plant_id: int
    bom_number: str
    material_id: int
    bom_version: int
    bom_name: str
    bom_type: str
    base_quantity: float
    unit_of_measure_id: int
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    is_active: bool
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    bom_lines: List[BOMLineResponse] = []

    model_config = ConfigDict(from_attributes=True)


class BOMListResponse(BaseModel):
    """DTO for paginated BOM list response"""
    items: List[BOMHeaderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Generic error response"""
    detail: str


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    detail: list[dict]


class NotFoundErrorResponse(BaseModel):
    """Not found error response"""
    detail: str = "Resource not found"


class ConflictErrorResponse(BaseModel):
    """Conflict error response"""
    detail: str = "Conflict with current state"
