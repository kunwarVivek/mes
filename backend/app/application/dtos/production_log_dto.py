"""
Production Log DTOs for API request/response.

Pydantic models for validation and serialization of production log data.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class ProductionLogCreateRequest(BaseModel):
    """DTO for creating a new production log entry"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    plant_id: int = Field(..., gt=0, description="Plant ID")
    work_order_id: int = Field(..., gt=0, description="Work Order ID")
    operation_id: Optional[int] = Field(None, gt=0, description="Optional Operation ID")
    machine_id: Optional[int] = Field(None, gt=0, description="Optional Machine ID")
    quantity_produced: Decimal = Field(..., ge=0, description="Quantity produced (good parts)")
    quantity_scrapped: Decimal = Field(default=Decimal("0"), ge=0, description="Quantity scrapped")
    quantity_reworked: Decimal = Field(default=Decimal("0"), ge=0, description="Quantity reworked")
    operator_id: Optional[int] = Field(None, gt=0, description="Optional Operator ID")
    shift_id: Optional[int] = Field(None, gt=0, description="Optional Shift ID")
    notes: Optional[str] = Field(None, description="Optional notes")
    custom_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional JSONB metadata")

    model_config = ConfigDict(from_attributes=True)


class ProductionLogResponse(BaseModel):
    """DTO for production log response"""
    id: int
    organization_id: int
    plant_id: int
    work_order_id: int
    operation_id: Optional[int]
    machine_id: Optional[int]
    timestamp: datetime
    quantity_produced: Decimal
    quantity_scrapped: Decimal
    quantity_reworked: Decimal
    operator_id: Optional[int]
    shift_id: Optional[int]
    notes: Optional[str]
    custom_metadata: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class ProductionLogListResponse(BaseModel):
    """DTO for paginated production log list"""
    items: list[ProductionLogResponse]
    total: int
    page: int
    page_size: int


class ProductionSummaryResponse(BaseModel):
    """DTO for aggregated production statistics"""
    work_order_id: int
    total_produced: Decimal
    total_scrapped: Decimal
    total_reworked: Decimal
    yield_rate: Decimal
    log_count: int
    first_log: datetime
    last_log: datetime
