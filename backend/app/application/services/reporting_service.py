"""
Reporting Service - Business logic for reports and dashboards
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.reporting import Report, ReportExecution, Dashboard
from app.infrastructure.repositories.reporting_repository import (
    ReportRepository,
    ReportExecutionRepository,
    DashboardRepository,
)
from app.application.dtos.reporting_dto import (
    ReportCreateDTO,
    ReportUpdateDTO,
    ReportExecuteDTO,
    DashboardCreateDTO,
    DashboardUpdateDTO,
    DashboardDataRequest,
    KPICalculationRequest,
)


class ReportingService:
    """Service for Report operations"""

    def __init__(self, db: Session):
        self.db = db
        self.report_repo = ReportRepository(db)
        self.execution_repo = ReportExecutionRepository(db)

    # ========== Report Management ==========

    def create_report(self, dto: ReportCreateDTO, created_by: int) -> Report:
        """Create a new report"""
        # Check if report code already exists
        existing = self.report_repo.get_by_code(dto.organization_id, dto.report_code)
        if existing:
            raise ValueError(f"Report with code '{dto.report_code}' already exists")

        # Validate query definition structure
        self._validate_query_definition(dto.query_definition)

        return self.report_repo.create(dto, created_by)

    def get_report(self, report_id: int, user_id: Optional[int] = None,
                   user_role_ids: Optional[List[int]] = None) -> Optional[Report]:
        """Get report by ID with access check"""
        report = self.report_repo.get_by_id(report_id)
        if not report:
            return None

        # Check access permissions
        if user_id and not report.can_user_access(user_id, user_role_ids):
            raise PermissionError("User does not have access to this report")

        return report

    def list_reports(self, organization_id: int, skip: int = 0, limit: int = 100,
                    report_type: Optional[str] = None, category: Optional[str] = None,
                    include_system_reports: bool = True, user_id: Optional[int] = None) -> List[Report]:
        """List reports for an organization"""
        return self.report_repo.list(
            organization_id, skip, limit, report_type, category,
            include_system_reports, user_id
        )

    def update_report(self, report_id: int, dto: ReportUpdateDTO,
                     user_id: Optional[int] = None) -> Optional[Report]:
        """Update a report"""
        report = self.report_repo.get_by_id(report_id)
        if not report:
            return None

        # Check if user is the creator (for non-system reports)
        if not report.is_system_report and user_id and report.created_by != user_id:
            raise PermissionError("Only the report creator can update it")

        # Validate query definition if provided
        if dto.query_definition:
            self._validate_query_definition(dto.query_definition)

        return self.report_repo.update(report_id, dto)

    def delete_report(self, report_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a report"""
        report = self.report_repo.get_by_id(report_id)
        if not report:
            return False

        # Check if user is the creator
        if user_id and report.created_by != user_id:
            raise PermissionError("Only the report creator can delete it")

        return self.report_repo.delete(report_id)

    # ========== Report Execution ==========

    def execute_report(self, report_id: int, dto: ReportExecuteDTO,
                      user_id: Optional[int] = None) -> ReportExecution:
        """
        Execute a report.

        This creates an execution record and triggers the actual report generation.
        The execution can be async (via PGMQ) or synchronous depending on report size.
        """
        # Get the report
        report = self.report_repo.get_by_id(report_id)
        if not report:
            raise ValueError(f"Report with ID {report_id} not found")

        # Check if report is active
        if not report.is_active:
            raise ValueError("Cannot execute inactive report")

        # Create execution record
        execution = self.execution_repo.create(
            report_id=report_id,
            organization_id=report.organization_id,
            trigger_type='MANUAL',
            triggered_by=user_id,
            parameters=dto.parameters,
            export_format=dto.export_format or (report.export_formats[0] if report.export_formats else None)
        )

        # TODO: In production, this should be async via PGMQ
        # For now, execute synchronously
        try:
            self._execute_report_query(execution, report)
        except Exception as e:
            self.execution_repo.update_status(
                execution.id,
                'FAILED',
                error_message=str(e)
            )
            raise

        # Update last executed timestamp
        self.report_repo.update_last_executed_at(report_id)

        return execution

    def get_execution(self, execution_id: int) -> Optional[ReportExecution]:
        """Get report execution by ID"""
        return self.execution_repo.get_by_id(execution_id)

    def list_executions(self, report_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[ReportExecution], int]:
        """List executions for a report"""
        executions = self.execution_repo.list_by_report(report_id, skip, limit)
        total = self.execution_repo.count_by_report(report_id)
        return executions, total

    # ========== Private Helper Methods ==========

    def _validate_query_definition(self, query_def: Dict[str, Any]) -> None:
        """Validate the query definition structure"""
        required_fields = ['data_source']
        for field in required_fields:
            if field not in query_def:
                raise ValueError(f"Query definition must include '{field}'")

        # Validate data source
        valid_sources = [
            'production_logs', 'work_orders', 'ncr', 'materials',
            'machines', 'inspections', 'shipments', 'custom'
        ]
        if query_def['data_source'] not in valid_sources:
            raise ValueError(f"Invalid data_source. Must be one of {valid_sources}")

    def _execute_report_query(self, execution: ReportExecution, report: Report) -> None:
        """
        Execute the actual report query and update execution record.

        NOTE: This is a simplified implementation. In production, this should:
        1. Use pg_duckdb for analytics queries
        2. Support complex aggregations and joins
        3. Handle large result sets
        4. Generate exports (PDF, CSV, XLSX)
        5. Be executed asynchronously via PGMQ
        """
        start_time = datetime.now(timezone.utc)

        # Update status to RUNNING
        self.execution_repo.update_status(execution.id, 'RUNNING')

        # TODO: Implement actual query execution logic
        # For now, return a placeholder result
        result_data = {
            "columns": ["date", "value"],
            "rows": [
                {"date": "2025-11-01", "value": 100},
                {"date": "2025-11-02", "value": 150},
            ],
            "summary": {
                "total_rows": 2,
                "aggregations": {}
            }
        }

        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Update execution with results
        self.execution_repo.update_result(
            execution.id,
            result_count=len(result_data.get('rows', [])),
            result_data=result_data,
            execution_time_ms=execution_time_ms,
            rows_processed=len(result_data.get('rows', []))
        )


class DashboardService:
    """Service for Dashboard operations"""

    def __init__(self, db: Session):
        self.db = db
        self.dashboard_repo = DashboardRepository(db)
        self.report_repo = ReportRepository(db)

    # ========== Dashboard Management ==========

    def create_dashboard(self, dto: DashboardCreateDTO, created_by: int) -> Dashboard:
        """Create a new dashboard"""
        # Check if dashboard code already exists
        existing = self.dashboard_repo.get_by_code(dto.organization_id, dto.dashboard_code)
        if existing:
            raise ValueError(f"Dashboard with code '{dto.dashboard_code}' already exists")

        # Validate layout and widgets
        self._validate_dashboard_config(dto.layout_config, dto.widgets)

        return self.dashboard_repo.create(dto, created_by)

    def get_dashboard(self, dashboard_id: int, user_id: Optional[int] = None,
                     user_role_ids: Optional[List[int]] = None) -> Optional[Dashboard]:
        """Get dashboard by ID with access check"""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            return None

        # Check access permissions
        if user_id and not dashboard.can_user_access(user_id, user_role_ids):
            raise PermissionError("User does not have access to this dashboard")

        return dashboard

    def get_default_dashboard(self, organization_id: int) -> Optional[Dashboard]:
        """Get the default dashboard for an organization"""
        return self.dashboard_repo.get_default_dashboard(organization_id)

    def list_dashboards(self, organization_id: int, skip: int = 0, limit: int = 100,
                       dashboard_type: Optional[str] = None,
                       include_system_dashboards: bool = True,
                       user_id: Optional[int] = None) -> List[Dashboard]:
        """List dashboards for an organization"""
        return self.dashboard_repo.list(
            organization_id, skip, limit, dashboard_type,
            include_system_dashboards, user_id
        )

    def update_dashboard(self, dashboard_id: int, dto: DashboardUpdateDTO,
                        user_id: Optional[int] = None) -> Optional[Dashboard]:
        """Update a dashboard"""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            return None

        # Check if user is the creator (for non-system dashboards)
        if not dashboard.is_system_dashboard and user_id and dashboard.created_by != user_id:
            raise PermissionError("Only the dashboard creator can update it")

        # Validate layout and widgets if provided
        if dto.layout_config or dto.widgets:
            layout = dto.layout_config or dashboard.layout_config
            widgets = dto.widgets or dashboard.widgets
            self._validate_dashboard_config(layout, widgets)

        return self.dashboard_repo.update(dashboard_id, dto)

    def delete_dashboard(self, dashboard_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a dashboard"""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            return False

        # Check if user is the creator
        if user_id and dashboard.created_by != user_id:
            raise PermissionError("Only the dashboard creator can delete it")

        return self.dashboard_repo.delete(dashboard_id)

    # ========== Dashboard Data ==========

    def get_dashboard_data(self, dashboard_id: int, request: DashboardDataRequest,
                          user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get data for all widgets in a dashboard.

        NOTE: This is a simplified implementation. In production, this should:
        1. Execute queries for each widget in parallel
        2. Apply dashboard filters
        3. Cache results for refresh intervals
        4. Support real-time data updates via WebSocket
        """
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            raise ValueError(f"Dashboard with ID {dashboard_id} not found")

        # Merge dashboard default filters with request filters
        filters = {**(dashboard.default_filters or {}), **(request.filters or {})}

        # TODO: Execute queries for each widget
        # For now, return placeholder data
        widget_data = {}
        for widget_id, widget_config in dashboard.widgets.items():
            widget_data[widget_id] = {
                "status": "loaded",
                "data": {"value": 0, "trend": "+0%"},
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

        return {
            "dashboard_id": dashboard_id,
            "widget_data": widget_data,
            "generated_at": datetime.now(timezone.utc),
            "filters_applied": filters
        }

    # ========== Private Helper Methods ==========

    def _validate_dashboard_config(self, layout_config: Dict[str, Any], widgets: Dict[str, Any]) -> None:
        """Validate dashboard layout and widget configuration"""
        # Validate layout config
        if 'grid' not in layout_config:
            raise ValueError("Layout config must include 'grid' configuration")

        if 'widgets' not in layout_config:
            raise ValueError("Layout config must include 'widgets' array")

        # Validate that all widgets in layout exist in widgets dict
        layout_widget_ids = {w['id'] for w in layout_config['widgets']}
        widget_ids = set(widgets.keys())

        if layout_widget_ids != widget_ids:
            raise ValueError("Layout widgets must match widget definitions")


class KPIService:
    """Service for KPI calculations"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_kpi(self, request: KPICalculationRequest) -> Dict[str, Any]:
        """
        Calculate a specific KPI.

        NOTE: This is a simplified implementation. In production, this should:
        1. Use pg_duckdb for fast analytics
        2. Support multiple KPI types (OEE, FPY, OTD, etc.)
        3. Cache calculations
        4. Support drill-down analysis
        """
        kpi_type = request.kpi_type

        # TODO: Implement actual KPI calculations
        # For now, return placeholder values
        return {
            "kpi_type": kpi_type,
            "value": 85.5,
            "unit": "%",
            "trend": 2.3,
            "breakdown": {},
            "calculated_at": datetime.now(timezone.utc),
            "date_range": request.date_range
        }
