"""
Repository for Reporting and Dashboards
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timezone

from app.models.reporting import Report, ReportExecution, Dashboard
from app.application.dtos.reporting_dto import (
    ReportCreateDTO,
    ReportUpdateDTO,
    ReportExecuteDTO,
    DashboardCreateDTO,
    DashboardUpdateDTO,
)


class ReportRepository:
    """Repository for Report operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: ReportCreateDTO, created_by: int) -> Report:
        """Create a new report"""
        report = Report(
            organization_id=dto.organization_id,
            report_name=dto.report_name,
            report_code=dto.report_code,
            description=dto.description,
            report_type=dto.report_type,
            category=dto.category,
            query_definition=dto.query_definition,
            display_config=dto.display_config,
            is_scheduled=dto.is_scheduled,
            schedule_cron=dto.schedule_cron,
            schedule_config=dto.schedule_config,
            export_formats=dto.export_formats,
            auto_email=dto.auto_email,
            email_recipients=dto.email_recipients,
            created_by=created_by,
            is_public=dto.is_public,
            shared_with_users=dto.shared_with_users,
            shared_with_roles=dto.shared_with_roles,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: int) -> Optional[Report]:
        """Get report by ID"""
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_by_code(self, organization_id: int, report_code: str) -> Optional[Report]:
        """Get report by code within an organization"""
        return self.db.query(Report).filter(
            and_(
                Report.organization_id == organization_id,
                Report.report_code == report_code
            )
        ).first()

    def list(self, organization_id: int, skip: int = 0, limit: int = 100,
            report_type: Optional[str] = None, category: Optional[str] = None,
            include_system_reports: bool = True, user_id: Optional[int] = None) -> List[Report]:
        """List reports for an organization"""
        query = self.db.query(Report).filter(
            and_(
                Report.organization_id == organization_id,
                Report.is_active == True
            )
        )

        # Filter by report type
        if report_type:
            query = query.filter(Report.report_type == report_type)

        # Filter by category
        if category:
            query = query.filter(Report.category == category)

        # Filter system reports
        if not include_system_reports:
            query = query.filter(Report.is_system_report == False)

        # Filter by user access (public reports + created by user + shared with user)
        if user_id:
            query = query.filter(
                or_(
                    Report.is_public == True,
                    Report.created_by == user_id,
                    Report.shared_with_users.contains([user_id])
                )
            )

        return query.order_by(desc(Report.created_at)).offset(skip).limit(limit).all()

    def update(self, report_id: int, dto: ReportUpdateDTO) -> Optional[Report]:
        """Update report (only for non-system reports)"""
        report = self.get_by_id(report_id)
        if not report:
            return None

        # Prevent updates to system reports (except for sharing/status)
        if report.is_system_report:
            # Only allow updating sharing and status for system reports
            if dto.is_public is not None:
                report.is_public = dto.is_public
            if dto.shared_with_users is not None:
                report.shared_with_users = dto.shared_with_users
            if dto.shared_with_roles is not None:
                report.shared_with_roles = dto.shared_with_roles
            if dto.is_active is not None:
                report.is_active = dto.is_active
        else:
            # Update all fields for custom reports
            if dto.report_name:
                report.report_name = dto.report_name
            if dto.description is not None:
                report.description = dto.description
            if dto.query_definition is not None:
                report.query_definition = dto.query_definition
            if dto.display_config is not None:
                report.display_config = dto.display_config
            if dto.is_scheduled is not None:
                report.is_scheduled = dto.is_scheduled
            if dto.schedule_cron is not None:
                report.schedule_cron = dto.schedule_cron
            if dto.schedule_config is not None:
                report.schedule_config = dto.schedule_config
            if dto.export_formats is not None:
                report.export_formats = dto.export_formats
            if dto.auto_email is not None:
                report.auto_email = dto.auto_email
            if dto.email_recipients is not None:
                report.email_recipients = dto.email_recipients
            if dto.is_public is not None:
                report.is_public = dto.is_public
            if dto.shared_with_users is not None:
                report.shared_with_users = dto.shared_with_users
            if dto.shared_with_roles is not None:
                report.shared_with_roles = dto.shared_with_roles
            if dto.is_active is not None:
                report.is_active = dto.is_active

        self.db.commit()
        self.db.refresh(report)
        return report

    def delete(self, report_id: int) -> bool:
        """Delete report (only for non-system reports)"""
        report = self.get_by_id(report_id)
        if not report:
            return False

        # Prevent deletion of system reports
        if report.is_system_report:
            raise ValueError("Cannot delete system reports")

        self.db.delete(report)
        self.db.commit()
        return True

    def get_scheduled_reports(self, organization_id: int) -> List[Report]:
        """Get all active scheduled reports"""
        return self.db.query(Report).filter(
            and_(
                Report.organization_id == organization_id,
                Report.is_scheduled == True,
                Report.is_active == True
            )
        ).all()

    def update_last_executed_at(self, report_id: int) -> None:
        """Update the last_executed_at timestamp"""
        report = self.get_by_id(report_id)
        if report:
            report.last_executed_at = datetime.now(timezone.utc)
            self.db.commit()


class ReportExecutionRepository:
    """Repository for ReportExecution operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, report_id: int, organization_id: int, trigger_type: str,
              triggered_by: Optional[int] = None, parameters: Optional[dict] = None,
              export_format: Optional[str] = None) -> ReportExecution:
        """Create a new report execution"""
        execution = ReportExecution(
            organization_id=organization_id,
            report_id=report_id,
            execution_status='PENDING',
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            parameters=parameters,
            export_format=export_format,
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def get_by_id(self, execution_id: int) -> Optional[ReportExecution]:
        """Get report execution by ID"""
        return self.db.query(ReportExecution).options(
            joinedload(ReportExecution.report)
        ).filter(ReportExecution.id == execution_id).first()

    def list_by_report(self, report_id: int, skip: int = 0, limit: int = 100) -> List[ReportExecution]:
        """List executions for a specific report"""
        return self.db.query(ReportExecution).filter(
            ReportExecution.report_id == report_id
        ).order_by(desc(ReportExecution.started_at)).offset(skip).limit(limit).all()

    def list_by_organization(self, organization_id: int, skip: int = 0, limit: int = 100,
                            status: Optional[str] = None) -> List[ReportExecution]:
        """List executions for an organization"""
        query = self.db.query(ReportExecution).options(
            joinedload(ReportExecution.report)
        ).filter(
            ReportExecution.organization_id == organization_id
        )

        if status:
            query = query.filter(ReportExecution.execution_status == status)

        return query.order_by(desc(ReportExecution.started_at)).offset(skip).limit(limit).all()

    def update_status(self, execution_id: int, status: str, error_message: Optional[str] = None) -> Optional[ReportExecution]:
        """Update execution status"""
        execution = self.get_by_id(execution_id)
        if not execution:
            return None

        execution.execution_status = status
        if error_message:
            execution.error_message = error_message

        if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
            execution.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_result(self, execution_id: int, result_count: int, result_data: Optional[dict] = None,
                     result_file_path: Optional[str] = None, execution_time_ms: Optional[int] = None,
                     rows_processed: Optional[int] = None) -> Optional[ReportExecution]:
        """Update execution results"""
        execution = self.get_by_id(execution_id)
        if not execution:
            return None

        execution.result_count = result_count
        execution.result_data = result_data
        execution.result_file_path = result_file_path
        execution.execution_time_ms = execution_time_ms
        execution.rows_processed = rows_processed
        execution.execution_status = 'COMPLETED'
        execution.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def count_by_report(self, report_id: int) -> int:
        """Count executions for a report"""
        return self.db.query(func.count(ReportExecution.id)).filter(
            ReportExecution.report_id == report_id
        ).scalar()


class DashboardRepository:
    """Repository for Dashboard operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: DashboardCreateDTO, created_by: int) -> Dashboard:
        """Create a new dashboard"""
        dashboard = Dashboard(
            organization_id=dto.organization_id,
            dashboard_name=dto.dashboard_name,
            dashboard_code=dto.dashboard_code,
            description=dto.description,
            dashboard_type=dto.dashboard_type,
            layout_config=dto.layout_config,
            widgets=dto.widgets,
            default_filters=dto.default_filters,
            auto_refresh=dto.auto_refresh,
            refresh_interval_seconds=dto.refresh_interval_seconds,
            created_by=created_by,
            is_public=dto.is_public,
            shared_with_users=dto.shared_with_users,
            shared_with_roles=dto.shared_with_roles,
            is_default=dto.is_default,
            display_order=dto.display_order,
        )
        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def get_by_id(self, dashboard_id: int) -> Optional[Dashboard]:
        """Get dashboard by ID"""
        return self.db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()

    def get_by_code(self, organization_id: int, dashboard_code: str) -> Optional[Dashboard]:
        """Get dashboard by code within an organization"""
        return self.db.query(Dashboard).filter(
            and_(
                Dashboard.organization_id == organization_id,
                Dashboard.dashboard_code == dashboard_code
            )
        ).first()

    def get_default_dashboard(self, organization_id: int) -> Optional[Dashboard]:
        """Get the default dashboard for an organization"""
        return self.db.query(Dashboard).filter(
            and_(
                Dashboard.organization_id == organization_id,
                Dashboard.is_default == True,
                Dashboard.is_active == True
            )
        ).first()

    def list(self, organization_id: int, skip: int = 0, limit: int = 100,
            dashboard_type: Optional[str] = None, include_system_dashboards: bool = True,
            user_id: Optional[int] = None) -> List[Dashboard]:
        """List dashboards for an organization"""
        query = self.db.query(Dashboard).filter(
            and_(
                Dashboard.organization_id == organization_id,
                Dashboard.is_active == True
            )
        )

        # Filter by dashboard type
        if dashboard_type:
            query = query.filter(Dashboard.dashboard_type == dashboard_type)

        # Filter system dashboards
        if not include_system_dashboards:
            query = query.filter(Dashboard.is_system_dashboard == False)

        # Filter by user access (public dashboards + created by user + shared with user)
        if user_id:
            query = query.filter(
                or_(
                    Dashboard.is_public == True,
                    Dashboard.created_by == user_id,
                    Dashboard.shared_with_users.contains([user_id])
                )
            )

        return query.order_by(Dashboard.display_order, desc(Dashboard.created_at)).offset(skip).limit(limit).all()

    def update(self, dashboard_id: int, dto: DashboardUpdateDTO) -> Optional[Dashboard]:
        """Update dashboard (only for non-system dashboards)"""
        dashboard = self.get_by_id(dashboard_id)
        if not dashboard:
            return None

        # Prevent updates to system dashboards (except for sharing/status)
        if dashboard.is_system_dashboard:
            # Only allow updating sharing and status for system dashboards
            if dto.is_public is not None:
                dashboard.is_public = dto.is_public
            if dto.shared_with_users is not None:
                dashboard.shared_with_users = dto.shared_with_users
            if dto.shared_with_roles is not None:
                dashboard.shared_with_roles = dto.shared_with_roles
            if dto.is_active is not None:
                dashboard.is_active = dto.is_active
        else:
            # Update all fields for custom dashboards
            if dto.dashboard_name:
                dashboard.dashboard_name = dto.dashboard_name
            if dto.description is not None:
                dashboard.description = dto.description
            if dto.layout_config is not None:
                dashboard.layout_config = dto.layout_config
            if dto.widgets is not None:
                dashboard.widgets = dto.widgets
            if dto.default_filters is not None:
                dashboard.default_filters = dto.default_filters
            if dto.auto_refresh is not None:
                dashboard.auto_refresh = dto.auto_refresh
            if dto.refresh_interval_seconds is not None:
                dashboard.refresh_interval_seconds = dto.refresh_interval_seconds
            if dto.is_public is not None:
                dashboard.is_public = dto.is_public
            if dto.shared_with_users is not None:
                dashboard.shared_with_users = dto.shared_with_users
            if dto.shared_with_roles is not None:
                dashboard.shared_with_roles = dto.shared_with_roles
            if dto.is_default is not None:
                # If setting as default, unset other default dashboards
                if dto.is_default:
                    self.db.query(Dashboard).filter(
                        and_(
                            Dashboard.organization_id == dashboard.organization_id,
                            Dashboard.is_default == True,
                            Dashboard.id != dashboard.id
                        )
                    ).update({"is_default": False})
                dashboard.is_default = dto.is_default
            if dto.display_order is not None:
                dashboard.display_order = dto.display_order
            if dto.is_active is not None:
                dashboard.is_active = dto.is_active

        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def delete(self, dashboard_id: int) -> bool:
        """Delete dashboard (only for non-system dashboards)"""
        dashboard = self.get_by_id(dashboard_id)
        if not dashboard:
            return False

        # Prevent deletion of system dashboards
        if dashboard.is_system_dashboard:
            raise ValueError("Cannot delete system dashboards")

        self.db.delete(dashboard)
        self.db.commit()
        return True
