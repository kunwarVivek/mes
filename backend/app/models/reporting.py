"""
Reporting and Dashboard models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum


# Enums
class ReportType(str, Enum):
    """Report type enumeration"""
    KPI = "KPI"
    CUSTOM = "CUSTOM"
    SCHEDULED = "SCHEDULED"
    AD_HOC = "AD_HOC"


class ReportCategory(str, Enum):
    """Report category enumeration"""
    PRODUCTION = "PRODUCTION"
    QUALITY = "QUALITY"
    INVENTORY = "INVENTORY"
    MAINTENANCE = "MAINTENANCE"
    CUSTOM = "CUSTOM"


class ExecutionStatus(str, Enum):
    """Report execution status enumeration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TriggerType(str, Enum):
    """Report execution trigger type enumeration"""
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"
    API = "API"


class DashboardType(str, Enum):
    """Dashboard type enumeration"""
    OVERVIEW = "OVERVIEW"
    PRODUCTION = "PRODUCTION"
    QUALITY = "QUALITY"
    INVENTORY = "INVENTORY"
    MAINTENANCE = "MAINTENANCE"
    CUSTOM = "CUSTOM"


class Report(Base):
    """
    Report definition model.

    Supports:
    - KPI reports (OEE, FPY, OTD)
    - Custom reports with flexible query definitions
    - Scheduled report execution
    - Multi-format export (PDF, CSV, XLSX)
    - Report sharing and permissions
    """
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Report identification
    report_name = Column(String(200), nullable=False)
    report_code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String(50), nullable=False)  # KPI, CUSTOM, SCHEDULED, AD_HOC
    category = Column(String(100), nullable=True)

    # Report definition
    # Structure: {
    #   "data_source": "production_logs|work_orders|ncr|etc",
    #   "columns": [...],
    #   "filters": [...],
    #   "aggregations": [...],
    #   "joins": [...]
    # }
    query_definition = Column(JSONB, nullable=False)

    # Display configuration
    # Structure: {
    #   "chart_type": "bar|line|pie|table",
    #   "x_axis": "...",
    #   "y_axis": "...",
    #   "colors": [...],
    #   "format": {...}
    # }
    display_config = Column(JSONB, nullable=True)

    # Scheduling
    is_scheduled = Column(Boolean, nullable=False, default=False)
    schedule_cron = Column(String(100), nullable=True)  # Cron expression
    schedule_config = Column(JSONB, nullable=True)

    # Export options
    export_formats = Column(ARRAY(String), nullable=True)  # ['PDF', 'CSV', 'XLSX']
    auto_email = Column(Boolean, nullable=False, default=False)
    email_recipients = Column(ARRAY(String), nullable=True)

    # Ownership and permissions
    created_by = Column(Integer, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False)
    shared_with_users = Column(ARRAY(Integer), nullable=True)
    shared_with_roles = Column(ARRAY(Integer), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_system_report = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_executed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    executions = relationship("ReportExecution", back_populates="report", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'report_code', name='uq_report_code_per_org'),
        Index('idx_reports_org', 'organization_id'),
        Index('idx_reports_type', 'report_type'),
        Index('idx_reports_category', 'category'),
        Index('idx_reports_created_by', 'created_by'),
        Index('idx_reports_scheduled', 'is_scheduled', 'is_active'),
        CheckConstraint(
            "report_type IN ('KPI', 'CUSTOM', 'SCHEDULED', 'AD_HOC')",
            name='chk_report_type_valid'
        ),
    )

    def __repr__(self):
        return f"<Report(id={self.id}, code='{self.report_code}', name='{self.report_name}')>"

    def can_user_access(self, user_id: int, user_role_ids: list = None) -> bool:
        """
        Check if a user can access this report.

        Args:
            user_id: User ID
            user_role_ids: List of role IDs the user has

        Returns:
            True if user can access, False otherwise
        """
        # Creator always has access
        if self.created_by == user_id:
            return True

        # Public reports are accessible to all
        if self.is_public:
            return True

        # Check if user is in shared_with_users
        if self.shared_with_users and user_id in self.shared_with_users:
            return True

        # Check if any of user's roles are in shared_with_roles
        if self.shared_with_roles and user_role_ids:
            if any(role_id in self.shared_with_roles for role_id in user_role_ids):
                return True

        return False


class ReportExecution(Base):
    """
    Report execution history and results.

    Tracks:
    - Execution status and performance metrics
    - Execution parameters and filters
    - Result data and file paths
    - Error handling and debugging
    """
    __tablename__ = 'report_executions'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    report_id = Column(Integer, nullable=False, index=True)

    # Execution details
    execution_status = Column(String(50), nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    triggered_by = Column(Integer, nullable=True)  # User ID or NULL for scheduled
    trigger_type = Column(String(50), nullable=False)  # MANUAL, SCHEDULED, API

    # Execution metadata
    # Structure: {
    #   "date_range": {"start": "...", "end": "..."},
    #   "filters": {...},
    #   "plant_id": 123
    # }
    parameters = Column(JSONB, nullable=True)

    # Results
    result_count = Column(Integer, nullable=True)
    result_data = Column(JSONB, nullable=True)  # Store small results
    result_file_path = Column(String(500), nullable=True)  # Path to exported file
    export_format = Column(String(20), nullable=True)  # PDF, CSV, XLSX

    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    rows_processed = Column(Integer, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_stack_trace = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    report = relationship("Report", back_populates="executions")

    # Table constraints
    __table_args__ = (
        Index('idx_report_executions_org', 'organization_id'),
        Index('idx_report_executions_report', 'report_id'),
        Index('idx_report_executions_status', 'execution_status'),
        Index('idx_report_executions_started', 'started_at'),
        Index('idx_report_executions_trigger', 'trigger_type'),
        CheckConstraint(
            "execution_status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='chk_execution_status_valid'
        ),
        CheckConstraint(
            "trigger_type IN ('MANUAL', 'SCHEDULED', 'API')",
            name='chk_trigger_type_valid'
        ),
    )

    def __repr__(self):
        return f"<ReportExecution(id={self.id}, report_id={self.report_id}, status='{self.execution_status}')>"

    def is_completed(self) -> bool:
        """Check if execution is completed (success or failure)"""
        return self.execution_status in [ExecutionStatus.COMPLETED.value, ExecutionStatus.FAILED.value]

    def is_successful(self) -> bool:
        """Check if execution completed successfully"""
        return self.execution_status == ExecutionStatus.COMPLETED.value

    def get_duration_seconds(self) -> float:
        """Get execution duration in seconds"""
        if self.execution_time_ms:
            return self.execution_time_ms / 1000.0
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return 0.0


class Dashboard(Base):
    """
    Dashboard configuration model.

    Supports:
    - Flexible grid layout
    - Multiple widget types (KPI cards, charts, tables)
    - Auto-refresh capabilities
    - Dashboard sharing and permissions
    - Default dashboard per organization
    """
    __tablename__ = 'dashboards'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Dashboard identification
    dashboard_name = Column(String(200), nullable=False)
    dashboard_code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    dashboard_type = Column(String(50), nullable=False)  # OVERVIEW, PRODUCTION, QUALITY, etc.

    # Layout configuration
    # Structure: {
    #   "grid": {"columns": 12, "row_height": 100},
    #   "widgets": [
    #     {
    #       "id": "widget_1",
    #       "type": "kpi_card|chart|table",
    #       "position": {"x": 0, "y": 0, "w": 4, "h": 2},
    #       "config": {...}
    #     }
    #   ]
    # }
    layout_config = Column(JSONB, nullable=False)

    # Widget definitions
    # Structure: {
    #   "widget_1": {
    #     "title": "OEE",
    #     "type": "kpi_card",
    #     "data_source": "report_id|custom_query",
    #     "refresh_interval": 300,  // seconds
    #     "config": {...}
    #   }
    # }
    widgets = Column(JSONB, nullable=False)

    # Filters
    # Structure: {
    #   "date_range": "last_7_days",
    #   "plant_id": null,  // null = all plants
    #   "shift_id": null
    # }
    default_filters = Column(JSONB, nullable=True)

    # Auto-refresh
    auto_refresh = Column(Boolean, nullable=False, default=False)
    refresh_interval_seconds = Column(Integer, nullable=True)

    # Ownership and permissions
    created_by = Column(Integer, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False)
    shared_with_users = Column(ARRAY(Integer), nullable=True)
    shared_with_roles = Column(ARRAY(Integer), nullable=True)

    # Display settings
    is_default = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_system_dashboard = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'dashboard_code', name='uq_dashboard_code_per_org'),
        Index('idx_dashboards_org', 'organization_id'),
        Index('idx_dashboards_type', 'dashboard_type'),
        Index('idx_dashboards_created_by', 'created_by'),
        Index('idx_dashboards_default', 'organization_id', 'is_default'),
        CheckConstraint(
            "dashboard_type IN ('OVERVIEW', 'PRODUCTION', 'QUALITY', 'INVENTORY', 'MAINTENANCE', 'CUSTOM')",
            name='chk_dashboard_type_valid'
        ),
    )

    def __repr__(self):
        return f"<Dashboard(id={self.id}, code='{self.dashboard_code}', name='{self.dashboard_name}')>"

    def can_user_access(self, user_id: int, user_role_ids: list = None) -> bool:
        """
        Check if a user can access this dashboard.

        Args:
            user_id: User ID
            user_role_ids: List of role IDs the user has

        Returns:
            True if user can access, False otherwise
        """
        # Creator always has access
        if self.created_by == user_id:
            return True

        # Public dashboards are accessible to all
        if self.is_public:
            return True

        # Check if user is in shared_with_users
        if self.shared_with_users and user_id in self.shared_with_users:
            return True

        # Check if any of user's roles are in shared_with_roles
        if self.shared_with_roles and user_role_ids:
            if any(role_id in self.shared_with_roles for role_id in user_role_ids):
                return True

        return False

    def get_widget_count(self) -> int:
        """Get the number of widgets in this dashboard"""
        if not self.widgets:
            return 0
        return len(self.widgets)
