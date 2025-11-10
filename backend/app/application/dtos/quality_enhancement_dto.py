"""
DTOs for Quality Enhancement (Inspection Plans, SPC, Quality Measurements)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from decimal import Decimal


# ========== Inspection Plan DTOs ==========

class InspectionPlanCreateDTO(BaseModel):
    """DTO for creating an inspection plan"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    plant_id: Optional[int] = Field(None, gt=0, description="Plant ID")
    plan_code: str = Field(..., min_length=1, max_length=100, description="Plan code")
    plan_name: str = Field(..., min_length=1, max_length=200, description="Plan name")
    description: Optional[str] = Field(None, description="Description")
    plan_type: str = Field(..., description="Plan type")
    applies_to: str = Field(..., description="Scope of application")
    material_id: Optional[int] = Field(None, gt=0, description="Material ID if applicable")
    work_center_id: Optional[int] = Field(None, gt=0, description="Work center ID if applicable")
    frequency: str = Field(..., description="Inspection frequency")
    frequency_value: Optional[int] = Field(None, gt=0, description="Frequency value (e.g., every 100 units)")
    sample_size: Optional[int] = Field(None, gt=0, description="Sample size for inspection")
    spc_enabled: bool = Field(default=False, description="Enable SPC")
    control_limits_config: Optional[Dict[str, Any]] = Field(None, description="Control limits configuration")
    effective_date: Optional[date] = Field(None, description="Effective date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    instructions: Optional[str] = Field(None, description="Inspection instructions")
    acceptance_criteria: Optional[str] = Field(None, description="Acceptance criteria")
    created_by: int = Field(..., gt=0, description="Created by user ID")

    @field_validator('plan_type')
    @classmethod
    def validate_plan_type(cls, v):
        """Validate plan type"""
        valid_types = ['INCOMING', 'IN_PROCESS', 'FINAL', 'AUDIT']
        if v not in valid_types:
            raise ValueError(f'plan_type must be one of {valid_types}')
        return v

    @field_validator('applies_to')
    @classmethod
    def validate_applies_to(cls, v):
        """Validate applies_to"""
        valid_values = ['MATERIAL', 'WORK_ORDER', 'PRODUCT', 'PROCESS']
        if v not in valid_values:
            raise ValueError(f'applies_to must be one of {valid_values}')
        return v

    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v):
        """Validate frequency"""
        valid_frequencies = ['EVERY_UNIT', 'HOURLY', 'DAILY', 'WEEKLY', 'PERIODIC', 'ON_DEMAND']
        if v not in valid_frequencies:
            raise ValueError(f'frequency must be one of {valid_frequencies}')
        return v


class InspectionPlanUpdateDTO(BaseModel):
    """DTO for updating an inspection plan"""
    plan_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    material_id: Optional[int] = Field(None, gt=0)
    work_center_id: Optional[int] = Field(None, gt=0)
    frequency: Optional[str] = None
    frequency_value: Optional[int] = Field(None, gt=0)
    sample_size: Optional[int] = Field(None, gt=0)
    spc_enabled: Optional[bool] = None
    control_limits_config: Optional[Dict[str, Any]] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    instructions: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    is_active: Optional[bool] = None


class InspectionPlanApprovalDTO(BaseModel):
    """DTO for approving an inspection plan"""
    approved_by: int = Field(..., gt=0, description="User ID approving the plan")
    comments: Optional[str] = Field(None, description="Approval comments")


class InspectionPlanResponse(BaseModel):
    """DTO for inspection plan response"""
    id: int
    organization_id: int
    plant_id: Optional[int]
    plan_code: str
    plan_name: str
    description: Optional[str]
    plan_type: str
    applies_to: str
    material_id: Optional[int]
    work_center_id: Optional[int]
    frequency: str
    frequency_value: Optional[int]
    sample_size: Optional[int]
    spc_enabled: bool
    control_limits_config: Optional[Dict[str, Any]]
    approved_by: Optional[int]
    approved_date: Optional[datetime]
    effective_date: Optional[date]
    expiry_date: Optional[date]
    instructions: Optional[str]
    acceptance_criteria: Optional[str]
    is_active: bool
    revision: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int

    class Config:
        from_attributes = True


# ========== Inspection Point DTOs ==========

class InspectionPointCreateDTO(BaseModel):
    """DTO for creating an inspection point"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    inspection_plan_id: int = Field(..., gt=0, description="Inspection plan ID")
    point_code: str = Field(..., min_length=1, max_length=100, description="Point code")
    point_name: str = Field(..., min_length=1, max_length=200, description="Point name")
    description: Optional[str] = Field(None, description="Description")
    inspection_method: Optional[str] = Field(None, max_length=100, description="Inspection method")
    inspection_equipment: Optional[str] = Field(None, max_length=200, description="Inspection equipment")
    sequence: int = Field(default=0, ge=0, description="Display sequence")
    is_mandatory: bool = Field(default=True, description="Is mandatory check")
    is_critical: bool = Field(default=False, description="Is critical check")
    inspection_instructions: Optional[str] = Field(None, description="Instructions")
    acceptance_criteria: Optional[str] = Field(None, description="Acceptance criteria")


class InspectionPointUpdateDTO(BaseModel):
    """DTO for updating an inspection point"""
    point_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    inspection_method: Optional[str] = Field(None, max_length=100)
    inspection_equipment: Optional[str] = Field(None, max_length=200)
    sequence: Optional[int] = Field(None, ge=0)
    is_mandatory: Optional[bool] = None
    is_critical: Optional[bool] = None
    inspection_instructions: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    is_active: Optional[bool] = None


class InspectionPointResponse(BaseModel):
    """DTO for inspection point response"""
    id: int
    organization_id: int
    inspection_plan_id: int
    point_code: str
    point_name: str
    description: Optional[str]
    inspection_method: Optional[str]
    inspection_equipment: Optional[str]
    sequence: int
    is_mandatory: bool
    is_critical: bool
    inspection_instructions: Optional[str]
    acceptance_criteria: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ========== Inspection Characteristic DTOs ==========

class InspectionCharacteristicCreateDTO(BaseModel):
    """DTO for creating an inspection characteristic"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    inspection_point_id: int = Field(..., gt=0, description="Inspection point ID")
    characteristic_code: str = Field(..., min_length=1, max_length=100, description="Characteristic code")
    characteristic_name: str = Field(..., min_length=1, max_length=200, description="Characteristic name")
    description: Optional[str] = Field(None, description="Description")
    characteristic_type: str = Field(..., description="Type (VARIABLE or ATTRIBUTE)")
    data_type: str = Field(..., description="Data type (NUMERIC, BOOLEAN, TEXT)")
    unit_of_measure: Optional[str] = Field(None, max_length=50, description="Unit of measure")
    target_value: Optional[Decimal] = Field(None, description="Target value")
    lower_spec_limit: Optional[Decimal] = Field(None, description="Lower specification limit (LSL)")
    upper_spec_limit: Optional[Decimal] = Field(None, description="Upper specification limit (USL)")
    lower_control_limit: Optional[Decimal] = Field(None, description="Lower control limit (LCL)")
    upper_control_limit: Optional[Decimal] = Field(None, description="Upper control limit (UCL)")
    track_spc: bool = Field(default=False, description="Track SPC for this characteristic")
    control_chart_type: Optional[str] = Field(None, description="Control chart type")
    subgroup_size: Optional[int] = Field(None, gt=0, description="Subgroup size for SPC")
    allowed_values: Optional[List[str]] = Field(None, description="Allowed values for attributes")
    tolerance_type: Optional[str] = Field(None, description="Tolerance type")
    tolerance: Optional[Decimal] = Field(None, description="Tolerance value")
    sequence: int = Field(default=0, ge=0, description="Display sequence")

    @field_validator('characteristic_type')
    @classmethod
    def validate_characteristic_type(cls, v):
        """Validate characteristic type"""
        valid_types = ['VARIABLE', 'ATTRIBUTE']
        if v not in valid_types:
            raise ValueError(f'characteristic_type must be one of {valid_types}')
        return v

    @field_validator('data_type')
    @classmethod
    def validate_data_type(cls, v):
        """Validate data type"""
        valid_types = ['NUMERIC', 'BOOLEAN', 'TEXT']
        if v not in valid_types:
            raise ValueError(f'data_type must be one of {valid_types}')
        return v

    @field_validator('control_chart_type')
    @classmethod
    def validate_control_chart_type(cls, v):
        """Validate control chart type"""
        if v is None:
            return v
        valid_types = ['XBAR_R', 'XBAR_S', 'I_MR', 'P_CHART', 'NP_CHART', 'C_CHART', 'U_CHART']
        if v not in valid_types:
            raise ValueError(f'control_chart_type must be one of {valid_types}')
        return v


class InspectionCharacteristicUpdateDTO(BaseModel):
    """DTO for updating an inspection characteristic"""
    characteristic_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    target_value: Optional[Decimal] = None
    lower_spec_limit: Optional[Decimal] = None
    upper_spec_limit: Optional[Decimal] = None
    lower_control_limit: Optional[Decimal] = None
    upper_control_limit: Optional[Decimal] = None
    track_spc: Optional[bool] = None
    control_chart_type: Optional[str] = None
    subgroup_size: Optional[int] = Field(None, gt=0)
    allowed_values: Optional[List[str]] = None
    tolerance_type: Optional[str] = None
    tolerance: Optional[Decimal] = None
    sequence: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class InspectionCharacteristicResponse(BaseModel):
    """DTO for inspection characteristic response"""
    id: int
    organization_id: int
    inspection_point_id: int
    characteristic_code: str
    characteristic_name: str
    description: Optional[str]
    characteristic_type: str
    data_type: str
    unit_of_measure: Optional[str]
    target_value: Optional[Decimal]
    lower_spec_limit: Optional[Decimal]
    upper_spec_limit: Optional[Decimal]
    lower_control_limit: Optional[Decimal]
    upper_control_limit: Optional[Decimal]
    track_spc: bool
    control_chart_type: Optional[str]
    subgroup_size: Optional[int]
    allowed_values: Optional[List[str]]
    tolerance_type: Optional[str]
    tolerance: Optional[Decimal]
    is_active: bool
    sequence: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ========== Inspection Measurement DTOs ==========

class InspectionMeasurementCreateDTO(BaseModel):
    """DTO for creating an inspection measurement"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    characteristic_id: int = Field(..., gt=0, description="Characteristic ID")
    inspection_plan_id: int = Field(..., gt=0, description="Inspection plan ID")
    work_order_id: Optional[int] = Field(None, gt=0, description="Work order ID")
    material_id: Optional[int] = Field(None, gt=0, description="Material ID")
    lot_number: Optional[str] = Field(None, max_length=100, description="Lot number")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    measured_value: Optional[Decimal] = Field(None, description="Measured numeric value")
    measured_text: Optional[str] = Field(None, max_length=500, description="Measured text value")
    sample_number: Optional[int] = Field(None, gt=0, description="Sample number")
    subgroup_number: Optional[int] = Field(None, gt=0, description="Subgroup number")
    measured_by: int = Field(..., gt=0, description="User ID who performed measurement")
    measurement_timestamp: datetime = Field(..., description="Measurement timestamp")
    inspection_equipment_id: Optional[str] = Field(None, max_length=100, description="Equipment ID")
    environmental_conditions: Optional[Dict[str, Any]] = Field(None, description="Environmental conditions")
    notes: Optional[str] = Field(None, description="Measurement notes")


class InspectionMeasurementBulkCreateDTO(BaseModel):
    """DTO for creating multiple measurements at once"""
    measurements: List[InspectionMeasurementCreateDTO] = Field(..., min_length=1, description="List of measurements")


class InspectionMeasurementResponse(BaseModel):
    """DTO for inspection measurement response"""
    id: int
    organization_id: int
    characteristic_id: int
    inspection_plan_id: int
    work_order_id: Optional[int]
    material_id: Optional[int]
    lot_number: Optional[str]
    serial_number: Optional[str]
    measured_value: Optional[Decimal]
    measured_text: Optional[str]
    is_conforming: Optional[bool]
    deviation: Optional[Decimal]
    sample_number: Optional[int]
    subgroup_number: Optional[int]
    range_value: Optional[Decimal]
    moving_range: Optional[Decimal]
    is_out_of_control: bool
    control_violation_type: Optional[str]
    measured_by: int
    measurement_timestamp: datetime
    inspection_equipment_id: Optional[str]
    environmental_conditions: Optional[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== SPC Analytics DTOs ==========

class SPCAnalysisRequest(BaseModel):
    """DTO for requesting SPC analysis"""
    characteristic_id: int = Field(..., gt=0, description="Characteristic ID")
    start_date: Optional[datetime] = Field(None, description="Start date for analysis")
    end_date: Optional[datetime] = Field(None, description="End date for analysis")
    lot_number: Optional[str] = Field(None, description="Filter by lot number")
    work_order_id: Optional[int] = Field(None, gt=0, description="Filter by work order")


class SPCAnalysisResponse(BaseModel):
    """DTO for SPC analysis response"""
    characteristic_id: int
    characteristic_name: str
    measurement_count: int
    mean: Optional[Decimal]
    std_dev: Optional[Decimal]
    min_value: Optional[Decimal]
    max_value: Optional[Decimal]
    range: Optional[Decimal]
    ucl: Optional[Decimal]
    lcl: Optional[Decimal]
    usl: Optional[Decimal]
    lsl: Optional[Decimal]
    target: Optional[Decimal]
    cp: Optional[Decimal]
    cpk: Optional[Decimal]
    out_of_control_count: int
    conforming_count: int
    non_conforming_count: int
    capability_status: str  # CAPABLE, MARGINAL, INCAPABLE


class ControlChartDataRequest(BaseModel):
    """DTO for requesting control chart data"""
    characteristic_id: int = Field(..., gt=0, description="Characteristic ID")
    chart_type: str = Field(..., description="Chart type (XBAR_R, I_MR, etc.)")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    limit: int = Field(default=100, ge=1, le=1000, description="Number of data points")


class ControlChartDataPoint(BaseModel):
    """Single data point for control chart"""
    timestamp: datetime
    value: Decimal
    ucl: Optional[Decimal]
    lcl: Optional[Decimal]
    center_line: Decimal
    is_out_of_control: bool
    violation_type: Optional[str]


class ControlChartDataResponse(BaseModel):
    """DTO for control chart data response"""
    characteristic_id: int
    characteristic_name: str
    chart_type: str
    data_points: List[ControlChartDataPoint]
    ucl: Optional[Decimal]
    lcl: Optional[Decimal]
    center_line: Decimal
    usl: Optional[Decimal]
    lsl: Optional[Decimal]


# ========== FPY (First Pass Yield) DTOs ==========

class FPYCalculationRequest(BaseModel):
    """DTO for FPY calculation request"""
    plant_id: Optional[int] = Field(None, gt=0, description="Plant ID filter")
    material_id: Optional[int] = Field(None, gt=0, description="Material ID filter")
    work_order_id: Optional[int] = Field(None, gt=0, description="Work order ID filter")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")


class FPYResponse(BaseModel):
    """DTO for FPY response"""
    total_inspected: int
    total_passed: int
    total_failed: int
    fpy_percentage: Decimal
    defect_rate: Decimal
    period_start: datetime
    period_end: datetime
    breakdown_by_plan: Optional[Dict[str, Any]] = None
    breakdown_by_material: Optional[Dict[str, Any]] = None
