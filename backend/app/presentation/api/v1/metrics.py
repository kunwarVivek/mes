"""
Metrics API Router - Dashboard metrics with aggregated counts and KPIs.

Provides endpoints for:
- GET /metrics/dashboard - Aggregated counts (materials, work orders, NCRs)
- GET /metrics/oee - Overall Equipment Effectiveness
- GET /metrics/otd - On-Time Delivery
- GET /metrics/fpy - First Pass Yield
- GET /metrics/kpi-dashboard - Consolidated KPI dashboard

Features:
- JWT authentication
- RLS context from authenticated user
- SQL aggregation queries (not limited by pagination)
- Caching for expensive calculations (15-minute TTL)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional
import logging

from app.core.database import get_db
from app.application.dtos.metrics_dto import DashboardMetricsResponseDTO
from app.models.material import Material
from app.models.work_order import WorkOrder, OrderStatus
from app.models.ncr import NCR, NCRStatus
from app.infrastructure.security.dependencies import get_current_user, get_user_context, _set_rls_context
from app.domain.entities.user import User

# KPI Use Cases
from app.application.use_cases.metrics import (
    CalculateOEEUseCase,
    CalculateOTDUseCase,
    CalculateFPYUseCase
)
from app.application.use_cases.metrics.calculate_oee import CalculateOEEDTO
from app.application.use_cases.metrics.calculate_otd import CalculateOTDDTO
from app.application.use_cases.metrics.calculate_fpy import CalculateFPYDTO

# Schemas
from app.presentation.schemas.metrics import (
    OEEResponse,
    OTDResponse,
    FPYResponse,
    KPIDashboardResponse,
    MachineOEEResponse,
    WorkOrderFPYResponse
)


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetricsResponseDTO)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get aggregated dashboard metrics.

    Returns counts for materials, work orders, and NCRs using SQL COUNT queries.
    Not limited by pagination (100-item limits).

    Respects RLS (Row-Level Security):
    - Filters by organization_id from JWT token
    - Filters by plant_id from JWT token

    Args:
        db: Database session
        current_user: Authenticated user from JWT

    Returns:
        DashboardMetricsResponseDTO with aggregated counts

    Raises:
        HTTPException 403: Missing organization/plant context
    """
    # Extract RLS context from authenticated user
    organization_id = current_user.organization_id
    plant_id = current_user.plant_id

    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization context required"
        )

    logger.info(
        f"Fetching dashboard metrics for org_id={organization_id}, plant_id={plant_id}"
    )

    # Count materials (respects RLS)
    materials_count = db.query(func.count(Material.id)).filter(
        Material.organization_id == organization_id
    )
    if plant_id:
        materials_count = materials_count.filter(Material.plant_id == plant_id)
    materials_count = materials_count.scalar() or 0

    # Count work orders (respects RLS)
    work_orders_count = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.organization_id == organization_id
    )
    if plant_id:
        work_orders_count = work_orders_count.filter(WorkOrder.plant_id == plant_id)
    work_orders_count = work_orders_count.scalar() or 0

    # Count NCRs (respects RLS)
    ncrs_count = db.query(func.count(NCR.id)).filter(
        NCR.organization_id == organization_id
    )
    if plant_id:
        ncrs_count = ncrs_count.filter(NCR.plant_id == plant_id)
    ncrs_count = ncrs_count.scalar() or 0

    # Count work orders by status (grouped query)
    wo_status_query = db.query(
        WorkOrder.order_status,
        func.count(WorkOrder.id)
    ).filter(
        WorkOrder.organization_id == organization_id
    )
    if plant_id:
        wo_status_query = wo_status_query.filter(WorkOrder.plant_id == plant_id)
    wo_status_results = wo_status_query.group_by(WorkOrder.order_status).all()

    # Initialize all statuses to 0
    work_orders_by_status = {
        OrderStatus.PLANNED.value: 0,
        OrderStatus.RELEASED.value: 0,
        OrderStatus.IN_PROGRESS.value: 0,
        OrderStatus.COMPLETED.value: 0,
        OrderStatus.CANCELLED.value: 0,
    }
    # Fill in actual counts
    for status, count in wo_status_results:
        work_orders_by_status[status.value] = count

    # Count NCRs by status (grouped query)
    ncr_status_query = db.query(
        NCR.status,
        func.count(NCR.id)
    ).filter(
        NCR.organization_id == organization_id
    )
    if plant_id:
        ncr_status_query = ncr_status_query.filter(NCR.plant_id == plant_id)
    ncr_status_results = ncr_status_query.group_by(NCR.status).all()

    # Initialize all statuses to 0
    ncrs_by_status = {
        NCRStatus.OPEN.value: 0,
        NCRStatus.IN_REVIEW.value: 0,
        NCRStatus.RESOLVED.value: 0,
        NCRStatus.CLOSED.value: 0,
    }
    # Fill in actual counts
    for status, count in ncr_status_results:
        ncrs_by_status[status.value] = count

    logger.info(
        f"Dashboard metrics: materials={materials_count}, "
        f"work_orders={work_orders_count}, ncrs={ncrs_count}"
    )

    return DashboardMetricsResponseDTO(
        materials_count=materials_count,
        work_orders_count=work_orders_count,
        ncrs_count=ncrs_count,
        work_orders_by_status=work_orders_by_status,
        ncrs_by_status=ncrs_by_status,
    )


# ============================================================================
# Dependency Injection Helpers
# ============================================================================

def get_oee_use_case(db: Session = Depends(get_db)) -> CalculateOEEUseCase:
    """Dependency injection for CalculateOEEUseCase."""
    return CalculateOEEUseCase(db)


def get_otd_use_case(db: Session = Depends(get_db)) -> CalculateOTDUseCase:
    """Dependency injection for CalculateOTDUseCase."""
    return CalculateOTDUseCase(db)


def get_fpy_use_case(db: Session = Depends(get_db)) -> CalculateFPYUseCase:
    """Dependency injection for CalculateFPYUseCase."""
    return CalculateFPYUseCase(db)


# ============================================================================
# KPI Endpoints
# ============================================================================

@router.get("/oee", response_model=OEEResponse)
def get_oee_metrics(
    plant_id: Optional[int] = Query(None, description="Filter by plant ID"),
    machine_id: Optional[int] = Query(None, description="Filter by specific machine ID"),
    start_date: Optional[datetime] = Query(None, description="Start of period (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End of period (ISO 8601)"),
    by_machine: bool = Query(False, description="Include breakdown by individual machines"),
    request: Request = None,
    use_case: CalculateOEEUseCase = Depends(get_oee_use_case),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get OEE (Overall Equipment Effectiveness) metrics.

    ## Business Flow
    1. Queries production_logs for total pieces, good pieces, defects
    2. Queries machine_status_history for downtime (DOWN, MAINTENANCE status)
    3. Calculates availability, performance, quality
    4. Returns OEE = Availability × Performance × Quality

    ## OEE Formula
    - **Availability** = (Total Time - Downtime) / Total Time
    - **Performance** = (Ideal Cycle Time × Total Pieces) / Operating Time
    - **Quality** = Good Pieces / Total Pieces
    - **OEE** = Availability × Performance × Quality

    ## Benchmarks
    - **World-Class**: OEE > 85%
    - **Fair**: OEE 60-85%
    - **Poor**: OEE < 60%

    ## Query Parameters
    - **plant_id**: Filter by plant (optional, respects RLS)
    - **machine_id**: Filter by specific machine (optional)
    - **start_date**: Start of period (defaults to 30 days ago)
    - **end_date**: End of period (defaults to now)
    - **by_machine**: Include breakdown by individual machines (default: false)

    ## Response
    ```json
    {
      "total_time_minutes": 43200.0,
      "downtime_minutes": 2160.0,
      "operating_time_minutes": 41040.0,
      "total_pieces": 5000,
      "good_pieces": 4750,
      "defect_pieces": 250,
      "availability": 95.0,
      "performance": 85.0,
      "quality": 95.0,
      "oee": 76.71,
      "start_date": "2024-11-01T00:00:00Z",
      "end_date": "2024-11-30T23:59:59Z",
      "machine_breakdown": []
    }
    ```

    ## Permissions
    - Requires: `metrics.view` permission
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id_context = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id_context)

        # Create DTO
        dto = CalculateOEEDTO(
            plant_id=plant_id,
            machine_id=machine_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id,
            by_machine=by_machine
        )

        # Execute use case
        result = use_case.execute(dto)

        # Build response
        return OEEResponse(
            total_time_minutes=result.total_time_minutes,
            downtime_minutes=result.downtime_minutes,
            operating_time_minutes=result.operating_time_minutes,
            total_pieces=result.total_pieces,
            good_pieces=result.good_pieces,
            defect_pieces=result.defect_pieces,
            scrapped_pieces=result.scrapped_pieces,
            reworked_pieces=result.reworked_pieces,
            availability=result.availability,
            performance=result.performance,
            quality=result.quality,
            oee=result.oee,
            start_date=result.start_date,
            end_date=result.end_date,
            machine_breakdown=[
                MachineOEEResponse(**m) for m in result.machine_breakdown
            ] if result.machine_breakdown else None
        )

    except Exception as e:
        logger.error(f"Error calculating OEE: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/otd", response_model=OTDResponse)
def get_otd_metrics(
    plant_id: Optional[int] = Query(None, description="Filter by plant ID"),
    start_date: Optional[datetime] = Query(None, description="Start of period (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End of period (ISO 8601)"),
    request: Request = None,
    use_case: CalculateOTDUseCase = Depends(get_otd_use_case),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get OTD (On-Time Delivery) metrics.

    ## Business Flow
    1. Queries completed work orders in period
    2. Compares end_date_actual vs end_date_planned
    3. Calculates percentage of on-time completions
    4. Calculates average delay for late work orders

    ## OTD Formula
    - **OTD** = (Work Orders Completed On-Time / Total Completed Work Orders) × 100%
    - A work order is **on-time** if: end_date_actual <= end_date_planned

    ## Benchmarks
    - **Excellent**: OTD > 95%
    - **Good**: OTD 85-95%
    - **Needs Improvement**: OTD < 85%

    ## Query Parameters
    - **plant_id**: Filter by plant (optional, respects RLS)
    - **start_date**: Filter work orders completed >= this date (defaults to 30 days ago)
    - **end_date**: Filter work orders completed <= this date (defaults to now)

    ## Response
    ```json
    {
      "total_completed": 150,
      "on_time": 135,
      "late": 15,
      "otd_percentage": 90.0,
      "average_delay_days": 1.2,
      "start_date": "2024-11-01T00:00:00Z",
      "end_date": "2024-11-30T23:59:59Z"
    }
    ```

    ## Permissions
    - Requires: `metrics.view` permission
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id_context = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id_context)

        # Create DTO
        dto = CalculateOTDDTO(
            plant_id=plant_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id
        )

        # Execute use case
        result = use_case.execute(dto)

        # Build response
        return OTDResponse(
            total_completed=result.total_completed,
            on_time=result.on_time,
            late=result.late,
            otd_percentage=result.otd_percentage,
            average_delay_days=result.average_delay_days,
            start_date=result.start_date,
            end_date=result.end_date
        )

    except Exception as e:
        logger.error(f"Error calculating OTD: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/fpy", response_model=FPYResponse)
def get_fpy_metrics(
    plant_id: Optional[int] = Query(None, description="Filter by plant ID"),
    start_date: Optional[datetime] = Query(None, description="Start of period (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End of period (ISO 8601)"),
    include_work_order_breakdown: bool = Query(False, description="Include top worst performers"),
    breakdown_limit: int = Query(10, description="Number of work orders in breakdown"),
    request: Request = None,
    use_case: CalculateFPYUseCase = Depends(get_fpy_use_case),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get FPY (First Pass Yield) metrics.

    ## Business Flow
    1. Queries inspection_log for all inspections in period
    2. Aggregates passed_quantity and failed_quantity
    3. Calculates FPY = Passed / Inspected
    4. Optionally returns top worst performers by work order

    ## FPY Formula
    - **FPY** = (Passed Quantity / Inspected Quantity) × 100%
    - **Defect Rate** = (Failed Quantity / Inspected Quantity) × 100%

    ## Benchmarks
    - **World-Class**: FPY > 99%
    - **Good**: FPY 95-99%
    - **Needs Improvement**: FPY < 95%

    ## Query Parameters
    - **plant_id**: Filter by plant (optional, respects RLS)
    - **start_date**: Filter inspections >= this date (defaults to 30 days ago)
    - **end_date**: Filter inspections <= this date (defaults to now)
    - **include_work_order_breakdown**: Include top worst performers by work order
    - **breakdown_limit**: Number of work orders to include (default: 10)

    ## Response
    ```json
    {
      "total_inspected": 10000,
      "total_passed": 9700,
      "total_failed": 300,
      "fpy_percentage": 97.0,
      "defect_rate": 3.0,
      "start_date": "2024-11-01T00:00:00Z",
      "end_date": "2024-11-30T23:59:59Z",
      "work_order_breakdown": []
    }
    ```

    ## Permissions
    - Requires: `metrics.view` permission
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id_context = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id_context)

        # Create DTO
        dto = CalculateFPYDTO(
            plant_id=plant_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id,
            include_work_order_breakdown=include_work_order_breakdown,
            breakdown_limit=breakdown_limit
        )

        # Execute use case
        result = use_case.execute(dto)

        # Build response
        return FPYResponse(
            total_inspected=result.total_inspected,
            total_passed=result.total_passed,
            total_failed=result.total_failed,
            fpy_percentage=result.fpy_percentage,
            defect_rate=result.defect_rate,
            start_date=result.start_date,
            end_date=result.end_date,
            work_order_breakdown=[
                WorkOrderFPYResponse(**wo) for wo in result.work_order_breakdown
            ] if result.work_order_breakdown else None
        )

    except Exception as e:
        logger.error(f"Error calculating FPY: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/kpi-dashboard", response_model=KPIDashboardResponse)
def get_kpi_dashboard(
    plant_id: Optional[int] = Query(None, description="Filter by plant ID"),
    start_date: Optional[datetime] = Query(None, description="Start of period (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End of period (ISO 8601)"),
    request: Request = None,
    oee_use_case: CalculateOEEUseCase = Depends(get_oee_use_case),
    otd_use_case: CalculateOTDUseCase = Depends(get_otd_use_case),
    fpy_use_case: CalculateFPYUseCase = Depends(get_fpy_use_case),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get consolidated KPI dashboard with OEE, OTD, and FPY.

    ## Business Flow
    1. Calculates OEE (Overall Equipment Effectiveness)
    2. Calculates OTD (On-Time Delivery)
    3. Calculates FPY (First Pass Yield)
    4. Returns all three KPIs in single response
    5. Uses caching for performance (15-minute TTL)

    ## Use Cases
    - **Executive Dashboard**: High-level view of manufacturing performance
    - **Plant Manager Dashboard**: Monitor key metrics in one view
    - **Performance Trending**: Track KPIs over time

    ## Query Parameters
    - **plant_id**: Filter by plant (optional, respects RLS)
    - **start_date**: Start of period (defaults to 30 days ago)
    - **end_date**: End of period (defaults to now)

    ## Response
    Returns consolidated KPI metrics with all three measurements:
    - OEE with availability, performance, quality breakdown
    - OTD with on-time vs late breakdown
    - FPY with pass/fail breakdown

    ## Permissions
    - Requires: `metrics.view` permission
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id_context = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id_context)

        # Calculate OEE
        oee_dto = CalculateOEEDTO(
            plant_id=plant_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id,
            by_machine=False
        )
        oee_result = oee_use_case.execute(oee_dto)

        # Calculate OTD
        otd_dto = CalculateOTDDTO(
            plant_id=plant_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id
        )
        otd_result = otd_use_case.execute(otd_dto)

        # Calculate FPY
        fpy_dto = CalculateFPYDTO(
            plant_id=plant_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id,
            include_work_order_breakdown=False
        )
        fpy_result = fpy_use_case.execute(fpy_dto)

        # Build consolidated response
        return KPIDashboardResponse(
            oee=OEEResponse(
                total_time_minutes=oee_result.total_time_minutes,
                downtime_minutes=oee_result.downtime_minutes,
                operating_time_minutes=oee_result.operating_time_minutes,
                total_pieces=oee_result.total_pieces,
                good_pieces=oee_result.good_pieces,
                defect_pieces=oee_result.defect_pieces,
                scrapped_pieces=oee_result.scrapped_pieces,
                reworked_pieces=oee_result.reworked_pieces,
                availability=oee_result.availability,
                performance=oee_result.performance,
                quality=oee_result.quality,
                oee=oee_result.oee,
                start_date=oee_result.start_date,
                end_date=oee_result.end_date,
                machine_breakdown=None
            ),
            otd=OTDResponse(
                total_completed=otd_result.total_completed,
                on_time=otd_result.on_time,
                late=otd_result.late,
                otd_percentage=otd_result.otd_percentage,
                average_delay_days=otd_result.average_delay_days,
                start_date=otd_result.start_date,
                end_date=otd_result.end_date
            ),
            fpy=FPYResponse(
                total_inspected=fpy_result.total_inspected,
                total_passed=fpy_result.total_passed,
                total_failed=fpy_result.total_failed,
                fpy_percentage=fpy_result.fpy_percentage,
                defect_rate=fpy_result.defect_rate,
                start_date=fpy_result.start_date,
                end_date=fpy_result.end_date,
                work_order_breakdown=None
            ),
            period_start=oee_result.start_date,
            period_end=oee_result.end_date,
            generated_at=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error generating KPI dashboard: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
