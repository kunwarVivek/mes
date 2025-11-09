"""
Data Transfer Objects (DTOs) for Material API.

Pydantic v2 schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

from app.models.material import ProcurementType, MRPType


class MaterialCreateRequest(BaseModel):
    """DTO for creating a new material"""
    organization_id: int = Field(gt=0, description="Organization ID")
    plant_id: int = Field(gt=0, description="Plant ID")
    material_number: str = Field(max_length=10, description="Unique material number (uppercase alphanumeric)")
    material_name: str = Field(max_length=200, min_length=1, description="Material name")
    description: Optional[str] = Field(default=None, max_length=500, description="Material description")
    material_category_id: int = Field(gt=0, description="Material category ID")
    base_uom_id: int = Field(gt=0, description="Base unit of measure ID")
    procurement_type: ProcurementType = Field(description="Procurement type")
    mrp_type: MRPType = Field(description="MRP type")
    safety_stock: Optional[float] = Field(default=0.0, ge=0, description="Safety stock quantity")
    reorder_point: Optional[float] = Field(default=0.0, ge=0, description="Reorder point quantity")
    lot_size: Optional[float] = Field(default=1.0, gt=0, description="Lot size for procurement")
    lead_time_days: Optional[int] = Field(default=0, ge=0, description="Procurement lead time in days")

    @field_validator('material_number')
    @classmethod
    def validate_material_number(cls, v: str) -> str:
        """Validate material number format (uppercase alphanumeric)"""
        if not re.match(r'^[A-Z0-9]+$', v):
            raise ValueError('material_number must be uppercase alphanumeric only')
        return v


class MaterialUpdateRequest(BaseModel):
    """DTO for updating an existing material (partial updates)"""
    material_name: Optional[str] = Field(default=None, max_length=200, min_length=1)
    description: Optional[str] = Field(default=None, max_length=500)
    material_category_id: Optional[int] = Field(default=None, gt=0)
    procurement_type: Optional[ProcurementType] = None
    mrp_type: Optional[MRPType] = None
    safety_stock: Optional[float] = Field(default=None, ge=0)
    reorder_point: Optional[float] = Field(default=None, ge=0)
    lot_size: Optional[float] = Field(default=None, gt=0)
    lead_time_days: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class MaterialResponse(BaseModel):
    """DTO for material response"""
    id: int
    organization_id: int
    plant_id: int
    material_number: str
    material_name: str
    description: Optional[str] = None
    material_category_id: int
    base_uom_id: int
    procurement_type: str
    mrp_type: str
    safety_stock: float
    reorder_point: float
    lot_size: float
    lead_time_days: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MaterialListResponse(BaseModel):
    """DTO for paginated material list response"""
    items: list[MaterialResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MaterialSearchResult(BaseModel):
    """DTO for material search result (single item)"""
    id: int
    organization_id: int
    plant_id: int
    material_number: str
    material_name: str
    description: Optional[str] = None
    material_category_id: int
    base_uom_id: int
    procurement_type: str
    mrp_type: str
    safety_stock: float
    reorder_point: float
    lot_size: float
    lead_time_days: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Generic error response"""
    detail: str


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    detail: list[dict]


class NotFoundErrorResponse(BaseModel):
    """Not found error response"""
    detail: str = "Resource not found"


class BarcodeGenerateRequest(BaseModel):
    """DTO for barcode generation request"""
    format: Optional[str] = Field(default="CODE128", description="Barcode format (CODE128, CODE39, EAN13, QR_CODE)")
    include_qr: Optional[bool] = Field(default=False, description="Include QR code with material details")

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate barcode format"""
        allowed_formats = ["CODE128", "CODE39", "EAN13", "QR_CODE"]
        if v not in allowed_formats:
            raise ValueError(f'format must be one of {allowed_formats}')
        return v


class BarcodeResponse(BaseModel):
    """DTO for barcode generation response"""
    material_number: str
    format: str
    barcode_image: str = Field(description="Base64-encoded barcode image (PNG)")
    qr_image: Optional[str] = Field(default=None, description="Base64-encoded QR code image (PNG, optional)")
