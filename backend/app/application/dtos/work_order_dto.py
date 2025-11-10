"""
Data Transfer Objects (DTOs) for Work Order API.

Pydantic v2 schemas for request/response validation.
Phase 3 Component 5: Work Order API DTOs
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.work_order import OrderType, OrderStatus, OperationStatus


class WorkOrderCreateRequest(BaseModel):
    """DTO for creating a new work order"""
    material_id: int = Field(gt=0, description="Material ID for finished good")
    order_type: OrderType = Field(default=OrderType.PRODUCTION, description="Order type (PRODUCTION, REWORK, ASSEMBLY)")
    planned_quantity: float = Field(gt=0, description="Planned production quantity (must be positive)")
    start_date_planned: Optional[datetime] = Field(default=None, description="Planned start date")
    end_date_planned: Optional[datetime] = Field(default=None, description="Planned end date")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1-10, 10 is highest)")

    @field_validator('planned_quantity')
    @classmethod
    def validate_planned_quantity(cls, v: float) -> float:
        """Validate planned quantity is positive"""
        if v <= 0:
            raise ValueError('planned_quantity must be positive')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Validate priority is in range 1-10"""
        if v < 1 or v > 10:
            raise ValueError('priority must be between 1 and 10')
        return v


class WorkOrderUpdateRequest(BaseModel):
    """DTO for updating an existing work order (partial updates)"""
    planned_quantity: Optional[float] = Field(default=None, gt=0)
    start_date_planned: Optional[datetime] = None
    end_date_planned: Optional[datetime] = None
    priority: Optional[int] = Field(default=None, ge=1, le=10)


class WorkOrderOperationResponse(BaseModel):
    """DTO for work order operation response"""
    id: int
    organization_id: int
    plant_id: int
    work_order_id: int
    operation_number: int
    operation_name: str
    work_center_id: int
    setup_time_minutes: float
    run_time_per_unit_minutes: float
    status: str
    actual_setup_time: Optional[float] = None
    actual_run_time: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkOrderMaterialResponse(BaseModel):
    """DTO for work order material response"""
    id: int
    work_order_id: int
    material_id: int
    planned_quantity: float
    actual_quantity: float
    unit_of_measure_id: int
    backflush: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkOrderResponse(BaseModel):
    """DTO for work order response"""
    id: int
    organization_id: int
    plant_id: int
    work_order_number: str
    material_id: int
    order_type: str
    order_status: str
    planned_quantity: float
    actual_quantity: float
    start_date_planned: Optional[datetime] = None
    start_date_actual: Optional[datetime] = None
    end_date_planned: Optional[datetime] = None
    end_date_actual: Optional[datetime] = None
    priority: int
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    operations: List[WorkOrderOperationResponse] = []
    materials: List[WorkOrderMaterialResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WorkOrderListResponse(BaseModel):
    """DTO for paginated work order list response"""
    items: List[WorkOrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class WorkOrderOperationCreateRequest(BaseModel):
    """DTO for adding operation to work order"""
    operation_number: int = Field(gt=0, description="Operation sequence number (must be positive)")
    operation_name: str = Field(max_length=100, description="Operation name")
    work_center_id: int = Field(gt=0, description="Work center ID")
    setup_time_minutes: float = Field(default=0.0, ge=0, description="Setup time in minutes")
    run_time_per_unit_minutes: float = Field(default=0.0, ge=0, description="Run time per unit in minutes")

    @field_validator('operation_number')
    @classmethod
    def validate_operation_number(cls, v: int) -> int:
        """Validate operation number is positive"""
        if v <= 0:
            raise ValueError('operation_number must be positive')
        return v


class WorkOrderMaterialCreateRequest(BaseModel):
    """DTO for adding material consumption to work order"""
    material_id: int = Field(gt=0, description="Material ID")
    planned_quantity: float = Field(gt=0, description="Planned consumption quantity")
    unit_of_measure_id: int = Field(gt=0, description="Unit of measure ID")
    backflush: bool = Field(default=False, description="Auto-consume on completion")

    @field_validator('planned_quantity')
    @classmethod
    def validate_planned_quantity(cls, v: float) -> float:
        """Validate planned quantity is positive"""
        if v <= 0:
            raise ValueError('planned_quantity must be positive')
        return v


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


class WorkOrderCostBreakdownResponse(BaseModel):
    """DTO for work order cost breakdown response"""
    work_order_id: int
    work_order_number: str
    quantity_ordered: float
    quantity_completed: float
    costs: dict = Field(description="Cost breakdown (material, labor, overhead, total)")
    cost_per_unit: dict = Field(description="Cost per unit breakdown")
    overhead_rate: float = Field(description="Overhead rate percentage")
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkOrderCostVarianceResponse(BaseModel):
    """DTO for work order cost variance analysis"""
    work_order_id: int
    work_order_number: str
    actual_costs: dict = Field(description="Actual costs (material, labor, overhead, total)")
    standard_costs: dict = Field(description="Standard/estimated costs (material, labor, overhead, total)")
    variance: dict = Field(description="Variance amounts (actual - standard)")
    variance_percentage: dict = Field(description="Variance percentages")

    model_config = ConfigDict(from_attributes=True)
