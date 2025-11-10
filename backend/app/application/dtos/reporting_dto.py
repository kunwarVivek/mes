"""
DTOs for Reporting and Dashboards
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime


# ========== Report DTOs ==========

class ReportCreateDTO(BaseModel):
    """DTO for creating a new report"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    report_name: str = Field(..., min_length=1, max_length=200, description="Report name")
    report_code: str = Field(..., min_length=1, max_length=100, description="Unique report code")
    description: Optional[str] = Field(None, description="Report description")
    report_type: str = Field(..., description="Report type (KPI, CUSTOM, SCHEDULED, AD_HOC)")
    category: Optional[str] = Field(None, description="Report category")
    query_definition: Dict[str, Any] = Field(..., description="Query definition JSON")
    display_config: Optional[Dict[str, Any]] = Field(None, description="Display configuration JSON")
    is_scheduled: bool = Field(default=False, description="Is report scheduled")
    schedule_cron: Optional[str] = Field(None, description="Cron expression for scheduling")
    schedule_config: Optional[Dict[str, Any]] = Field(None, description="Schedule configuration")
    export_formats: Optional[List[str]] = Field(None, description="Export formats (PDF, CSV, XLSX)")
    auto_email: bool = Field(default=False, description="Auto-email report")
    email_recipients: Optional[List[str]] = Field(None, description="Email recipients")
    is_public: bool = Field(default=False, description="Is report public")
    shared_with_users: Optional[List[int]] = Field(None, description="User IDs to share with")
    shared_with_roles: Optional[List[int]] = Field(None, description="Role IDs to share with")

    @field_validator('report_code')
    @classmethod
    def validate_report_code(cls, v):
        """Ensure report_code is uppercase with underscores"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('report_code must be alphanumeric with underscores or hyphens')
        return v.upper()

    @field_validator('report_type')
    @classmethod
    def validate_report_type(cls, v):
        """Validate report type"""
        valid_types = ['KPI', 'CUSTOM', 'SCHEDULED', 'AD_HOC']
        if v not in valid_types:
            raise ValueError(f'report_type must be one of {valid_types}')
        return v

    @field_validator('export_formats')
    @classmethod
    def validate_export_formats(cls, v):
        """Validate export formats"""
        if v is None:
            return v
        valid_formats = ['PDF', 'CSV', 'XLSX', 'JSON']
        for fmt in v:
            if fmt not in valid_formats:
                raise ValueError(f'Invalid export format: {fmt}. Must be one of {valid_formats}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "report_name": "Production Summary",
                "report_code": "PRODUCTION_SUMMARY",
                "description": "Daily production summary report",
                "report_type": "CUSTOM",
                "category": "PRODUCTION",
                "query_definition": {
                    "data_source": "production_logs",
                    "columns": ["date", "total_quantity", "good_quantity"],
                    "aggregations": ["sum"],
                    "group_by": ["date"]
                },
                "is_public": True
            }
        }


class ReportUpdateDTO(BaseModel):
    """DTO for updating a report"""
    report_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    query_definition: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    is_scheduled: Optional[bool] = None
    schedule_cron: Optional[str] = None
    schedule_config: Optional[Dict[str, Any]] = None
    export_formats: Optional[List[str]] = None
    auto_email: Optional[bool] = None
    email_recipients: Optional[List[str]] = None
    is_public: Optional[bool] = None
    shared_with_users: Optional[List[int]] = None
    shared_with_roles: Optional[List[int]] = None
    is_active: Optional[bool] = None


class ReportResponse(BaseModel):
    """DTO for report response"""
    id: int
    organization_id: int
    report_name: str
    report_code: str
    description: Optional[str]
    report_type: str
    category: Optional[str]
    query_definition: Dict[str, Any]
    display_config: Optional[Dict[str, Any]]
    is_scheduled: bool
    schedule_cron: Optional[str]
    schedule_config: Optional[Dict[str, Any]]
    export_formats: Optional[List[str]]
    auto_email: bool
    email_recipients: Optional[List[str]]
    created_by: int
    is_public: bool
    shared_with_users: Optional[List[int]]
    shared_with_roles: Optional[List[int]]
    is_active: bool
    is_system_report: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_executed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReportExecuteDTO(BaseModel):
    """DTO for executing a report"""
    parameters: Optional[Dict[str, Any]] = Field(None, description="Execution parameters")
    export_format: Optional[str] = Field(None, description="Export format (PDF, CSV, XLSX)")

    @field_validator('export_format')
    @classmethod
    def validate_export_format(cls, v):
        """Validate export format"""
        if v is None:
            return v
        valid_formats = ['PDF', 'CSV', 'XLSX', 'JSON']
        if v not in valid_formats:
            raise ValueError(f'export_format must be one of {valid_formats}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "parameters": {
                    "date_range": {"start": "2025-11-01", "end": "2025-11-10"},
                    "plant_id": 1,
                    "filters": {"material_type": "FINISHED_GOOD"}
                },
                "export_format": "PDF"
            }
        }


# ========== Report Execution DTOs ==========

class ReportExecutionResponse(BaseModel):
    """DTO for report execution response"""
    id: int
    organization_id: int
    report_id: int
    execution_status: str
    triggered_by: Optional[int]
    trigger_type: str
    parameters: Optional[Dict[str, Any]]
    result_count: Optional[int]
    result_data: Optional[Dict[str, Any]]
    result_file_path: Optional[str]
    export_format: Optional[str]
    execution_time_ms: Optional[int]
    rows_processed: Optional[int]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReportExecutionListResponse(BaseModel):
    """DTO for paginated report execution list"""
    total: int
    executions: List[ReportExecutionResponse]
    skip: int
    limit: int


# ========== Dashboard DTOs ==========

class DashboardCreateDTO(BaseModel):
    """DTO for creating a new dashboard"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    dashboard_name: str = Field(..., min_length=1, max_length=200, description="Dashboard name")
    dashboard_code: str = Field(..., min_length=1, max_length=100, description="Unique dashboard code")
    description: Optional[str] = Field(None, description="Dashboard description")
    dashboard_type: str = Field(..., description="Dashboard type")
    layout_config: Dict[str, Any] = Field(..., description="Layout configuration JSON")
    widgets: Dict[str, Any] = Field(..., description="Widget definitions JSON")
    default_filters: Optional[Dict[str, Any]] = Field(None, description="Default filters")
    auto_refresh: bool = Field(default=False, description="Enable auto-refresh")
    refresh_interval_seconds: Optional[int] = Field(None, description="Refresh interval in seconds")
    is_public: bool = Field(default=False, description="Is dashboard public")
    shared_with_users: Optional[List[int]] = Field(None, description="User IDs to share with")
    shared_with_roles: Optional[List[int]] = Field(None, description="Role IDs to share with")
    is_default: bool = Field(default=False, description="Is default dashboard")
    display_order: int = Field(default=0, description="Display order")

    @field_validator('dashboard_code')
    @classmethod
    def validate_dashboard_code(cls, v):
        """Ensure dashboard_code is uppercase with underscores"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('dashboard_code must be alphanumeric with underscores or hyphens')
        return v.upper()

    @field_validator('dashboard_type')
    @classmethod
    def validate_dashboard_type(cls, v):
        """Validate dashboard type"""
        valid_types = ['OVERVIEW', 'PRODUCTION', 'QUALITY', 'INVENTORY', 'MAINTENANCE', 'CUSTOM']
        if v not in valid_types:
            raise ValueError(f'dashboard_type must be one of {valid_types}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "dashboard_name": "Production Overview",
                "dashboard_code": "PRODUCTION_OVERVIEW",
                "description": "Main production dashboard",
                "dashboard_type": "PRODUCTION",
                "layout_config": {
                    "grid": {"columns": 12, "row_height": 100},
                    "widgets": [
                        {"id": "oee", "type": "kpi_card", "position": {"x": 0, "y": 0, "w": 4, "h": 2}}
                    ]
                },
                "widgets": {
                    "oee": {"title": "OEE", "type": "kpi_card", "data_source": "OEE_REPORT"}
                },
                "is_public": True
            }
        }


class DashboardUpdateDTO(BaseModel):
    """DTO for updating a dashboard"""
    dashboard_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    widgets: Optional[Dict[str, Any]] = None
    default_filters: Optional[Dict[str, Any]] = None
    auto_refresh: Optional[bool] = None
    refresh_interval_seconds: Optional[int] = None
    is_public: Optional[bool] = None
    shared_with_users: Optional[List[int]] = None
    shared_with_roles: Optional[List[int]] = None
    is_default: Optional[bool] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class DashboardResponse(BaseModel):
    """DTO for dashboard response"""
    id: int
    organization_id: int
    dashboard_name: str
    dashboard_code: str
    description: Optional[str]
    dashboard_type: str
    layout_config: Dict[str, Any]
    widgets: Dict[str, Any]
    default_filters: Optional[Dict[str, Any]]
    auto_refresh: bool
    refresh_interval_seconds: Optional[int]
    created_by: int
    is_public: bool
    shared_with_users: Optional[List[int]]
    shared_with_roles: Optional[List[int]]
    is_default: bool
    display_order: int
    is_active: bool
    is_system_dashboard: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class DashboardDataRequest(BaseModel):
    """DTO for requesting dashboard data"""
    filters: Optional[Dict[str, Any]] = Field(None, description="Dashboard filters")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter")

    class Config:
        json_schema_extra = {
            "example": {
                "filters": {
                    "plant_id": 1,
                    "shift_id": 2
                },
                "date_range": {
                    "start": "2025-11-01",
                    "end": "2025-11-10"
                }
            }
        }


class DashboardDataResponse(BaseModel):
    """DTO for dashboard data response"""
    dashboard_id: int
    widget_data: Dict[str, Any]  # Keyed by widget ID
    generated_at: datetime
    filters_applied: Optional[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "dashboard_id": 1,
                "widget_data": {
                    "oee": {"value": 85.5, "trend": "+2.3%", "status": "good"},
                    "fpy": {"value": 92.1, "trend": "-0.5%", "status": "warning"}
                },
                "generated_at": "2025-11-10T10:30:00Z",
                "filters_applied": {"plant_id": 1}
            }
        }


# ========== KPI DTOs ==========

class KPICalculationRequest(BaseModel):
    """DTO for KPI calculation request"""
    kpi_type: str = Field(..., description="KPI type (OEE, FPY, OTD, etc.)")
    date_range: Dict[str, str] = Field(..., description="Date range for calculation")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")

    @field_validator('kpi_type')
    @classmethod
    def validate_kpi_type(cls, v):
        """Validate KPI type"""
        valid_kpis = ['OEE', 'FPY', 'OTD', 'OQD', 'DOWNTIME', 'YIELD', 'THROUGHPUT']
        if v not in valid_kpis:
            raise ValueError(f'kpi_type must be one of {valid_kpis}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "kpi_type": "OEE",
                "date_range": {"start": "2025-11-01", "end": "2025-11-10"},
                "filters": {"machine_id": 5, "plant_id": 1}
            }
        }


class KPICalculationResponse(BaseModel):
    """DTO for KPI calculation response"""
    kpi_type: str
    value: float
    unit: str
    trend: Optional[float] = None  # Percentage change from previous period
    breakdown: Optional[Dict[str, Any]] = None  # Detailed breakdown
    calculated_at: datetime
    date_range: Dict[str, str]

    class Config:
        json_schema_extra = {
            "example": {
                "kpi_type": "OEE",
                "value": 85.5,
                "unit": "%",
                "trend": 2.3,
                "breakdown": {
                    "availability": 95.2,
                    "performance": 92.1,
                    "quality": 97.5
                },
                "calculated_at": "2025-11-10T10:30:00Z",
                "date_range": {"start": "2025-11-01", "end": "2025-11-10"}
            }
        }
