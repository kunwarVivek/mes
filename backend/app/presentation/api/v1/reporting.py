"""
API endpoints for Reporting and Dashboards
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.services.reporting_service import ReportingService, DashboardService, KPIService
from app.application.dtos.reporting_dto import (
    ReportCreateDTO,
    ReportUpdateDTO,
    ReportResponse,
    ReportExecuteDTO,
    ReportExecutionResponse,
    ReportExecutionListResponse,
    DashboardCreateDTO,
    DashboardUpdateDTO,
    DashboardResponse,
    DashboardDataRequest,
    DashboardDataResponse,
    KPICalculationRequest,
    KPICalculationResponse,
)

router = APIRouter()


# ========== Report Endpoints ==========

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED, tags=["reports"])
async def create_report(
    dto: ReportCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new report.

    **Requires:** Admin or Report Manager role
    """
    service = ReportingService(db)
    created_by = current_user.get("id")

    try:
        report = service.create_report(dto, created_by)
        return ReportResponse.from_orm(report)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/reports", response_model=List[ReportResponse], tags=["reports"])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    include_system: bool = Query(True, description="Include system reports"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all reports for the current organization.

    **Query Params:**
    - skip: Pagination offset
    - limit: Max results (default 100, max 1000)
    - report_type: Filter by report type (KPI, CUSTOM, etc.)
    - category: Filter by category (PRODUCTION, QUALITY, etc.)
    - include_system: Include system-defined reports
    """
    service = ReportingService(db)
    organization_id = current_user.get("organization_id")
    user_id = current_user.get("id")

    reports = service.list_reports(
        organization_id, skip, limit, report_type, category,
        include_system, user_id
    )
    return [ReportResponse.from_orm(report) for report in reports]


@router.get("/reports/{report_id}", response_model=ReportResponse, tags=["reports"])
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get report by ID"""
    service = ReportingService(db)
    user_id = current_user.get("id")

    try:
        report = service.get_report(report_id, user_id)
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        return ReportResponse.from_orm(report)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put("/reports/{report_id}", response_model=ReportResponse, tags=["reports"])
async def update_report(
    report_id: int,
    dto: ReportUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a report.

    **Note:** System reports have limited update capabilities
    """
    service = ReportingService(db)
    user_id = current_user.get("id")

    try:
        report = service.update_report(report_id, dto, user_id)
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        return ReportResponse.from_orm(report)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["reports"])
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a report.

    **Note:**
    - System reports cannot be deleted
    - Only the creator can delete custom reports
    """
    service = ReportingService(db)
    user_id = current_user.get("id")

    try:
        success = service.delete_report(report_id, user_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== Report Execution Endpoints ==========

@router.post("/reports/{report_id}/execute", response_model=ReportExecutionResponse,
            status_code=status.HTTP_202_ACCEPTED, tags=["reports"])
async def execute_report(
    report_id: int,
    dto: ReportExecuteDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Execute a report.

    **Returns:** 202 Accepted with execution details
    **Note:** Large reports are executed asynchronously
    """
    service = ReportingService(db)
    user_id = current_user.get("id")

    try:
        execution = service.execute_report(report_id, dto, user_id)
        return ReportExecutionResponse.from_orm(execution)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/reports/{report_id}/executions", response_model=ReportExecutionListResponse, tags=["reports"])
async def list_report_executions(
    report_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List execution history for a report"""
    service = ReportingService(db)

    executions, total = service.list_executions(report_id, skip, limit)
    return ReportExecutionListResponse(
        total=total,
        executions=[ReportExecutionResponse.from_orm(ex) for ex in executions],
        skip=skip,
        limit=limit
    )


@router.get("/executions/{execution_id}", response_model=ReportExecutionResponse, tags=["reports"])
async def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get report execution by ID"""
    service = ReportingService(db)

    execution = service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    return ReportExecutionResponse.from_orm(execution)


# ========== Dashboard Endpoints ==========

@router.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED, tags=["dashboards"])
async def create_dashboard(
    dto: DashboardCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new dashboard.

    **Requires:** Admin or Dashboard Manager role
    """
    service = DashboardService(db)
    created_by = current_user.get("id")

    try:
        dashboard = service.create_dashboard(dto, created_by)
        return DashboardResponse.from_orm(dashboard)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/dashboards", response_model=List[DashboardResponse], tags=["dashboards"])
async def list_dashboards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    dashboard_type: Optional[str] = Query(None, description="Filter by dashboard type"),
    include_system: bool = Query(True, description="Include system dashboards"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all dashboards for the current organization.

    **Query Params:**
    - skip: Pagination offset
    - limit: Max results (default 100, max 1000)
    - dashboard_type: Filter by type (OVERVIEW, PRODUCTION, etc.)
    - include_system: Include system-defined dashboards
    """
    service = DashboardService(db)
    organization_id = current_user.get("organization_id")
    user_id = current_user.get("id")

    dashboards = service.list_dashboards(
        organization_id, skip, limit, dashboard_type,
        include_system, user_id
    )
    return [DashboardResponse.from_orm(dashboard) for dashboard in dashboards]


@router.get("/dashboards/default", response_model=DashboardResponse, tags=["dashboards"])
async def get_default_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the default dashboard for the organization"""
    service = DashboardService(db)
    organization_id = current_user.get("organization_id")

    dashboard = service.get_default_dashboard(organization_id)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No default dashboard found")

    return DashboardResponse.from_orm(dashboard)


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse, tags=["dashboards"])
async def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard by ID"""
    service = DashboardService(db)
    user_id = current_user.get("id")

    try:
        dashboard = service.get_dashboard(dashboard_id, user_id)
        if not dashboard:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
        return DashboardResponse.from_orm(dashboard)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put("/dashboards/{dashboard_id}", response_model=DashboardResponse, tags=["dashboards"])
async def update_dashboard(
    dashboard_id: int,
    dto: DashboardUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a dashboard.

    **Note:** System dashboards have limited update capabilities
    """
    service = DashboardService(db)
    user_id = current_user.get("id")

    try:
        dashboard = service.update_dashboard(dashboard_id, dto, user_id)
        if not dashboard:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
        return DashboardResponse.from_orm(dashboard)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["dashboards"])
async def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a dashboard.

    **Note:**
    - System dashboards cannot be deleted
    - Only the creator can delete custom dashboards
    """
    service = DashboardService(db)
    user_id = current_user.get("id")

    try:
        success = service.delete_dashboard(dashboard_id, user_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/dashboards/{dashboard_id}/data", response_model=DashboardDataResponse, tags=["dashboards"])
async def get_dashboard_data(
    dashboard_id: int,
    request: DashboardDataRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get data for all widgets in a dashboard.

    **Use Case:** Frontend requests dashboard data with current filters
    """
    service = DashboardService(db)
    user_id = current_user.get("id")

    try:
        data = service.get_dashboard_data(dashboard_id, request, user_id)
        return DashboardDataResponse(**data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== KPI Endpoints ==========

@router.post("/kpis/calculate", response_model=KPICalculationResponse, tags=["kpis"])
async def calculate_kpi(
    request: KPICalculationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate a specific KPI.

    **Supported KPIs:**
    - OEE: Overall Equipment Effectiveness
    - FPY: First Pass Yield
    - OTD: On-Time Delivery
    - OQD: On-Quality Delivery
    - DOWNTIME: Machine downtime
    - YIELD: Production yield
    - THROUGHPUT: Production throughput
    """
    service = KPIService(db)

    try:
        result = service.calculate_kpi(request)
        return KPICalculationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
