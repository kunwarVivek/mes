"""
Metrics API Router - Dashboard metrics with aggregated counts.

Provides GET /metrics/dashboard endpoint with:
- JWT authentication
- RLS context from authenticated user
- SQL COUNT queries (not limited by pagination)
- Aggregated counts for materials, work orders, NCRs
- Status breakdowns for work orders and NCRs
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.core.database import get_db
from app.application.dtos.metrics_dto import DashboardMetricsResponseDTO
from app.models.material import Material
from app.models.work_order import WorkOrder, OrderStatus
from app.models.ncr import NCR, NCRStatus
from app.infrastructure.security.dependencies import get_current_user
from app.domain.entities.user import User


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
