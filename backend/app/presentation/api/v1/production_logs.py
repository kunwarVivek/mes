"""
Production Logs API Router.

RESTful endpoints for production logging.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from decimal import Decimal
import logging

from app.core.database import get_db
from app.application.dtos.production_log_dto import (
    ProductionLogCreateRequest,
    ProductionLogResponse,
    ProductionLogListResponse,
    ProductionSummaryResponse
)
from app.infrastructure.repositories.production_log_repository import ProductionLogRepository
from app.models.work_order import WorkOrder, WorkOrderMaterial, WorkOrderOperation, WorkCenter
from app.models.costing import MaterialCosting

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/", response_model=ProductionLogResponse, status_code=201)
def log_production(dto: ProductionLogCreateRequest, db: Session = Depends(get_db)):
    """
    Log new production entry and accumulate work order costs.

    Creates a new production log entry for a work order and calculates:
    - Material cost (based on quantity produced ratio)
    - Labor cost (based on operation time and work center cost per hour)
    - Overhead cost (50% of labor cost)
    - Total actual cost (sum of all costs)

    Args:
        dto: Production log create request
        db: Database session

    Returns:
        ProductionLogResponse: Created production log

    Raises:
        HTTPException: 404 if work order not found
    """
    repo = ProductionLogRepository(db)
    log = repo.create(dto)

    # Accumulate costs for the work order
    _accumulate_work_order_costs(db, log)

    return log


def _accumulate_work_order_costs(db: Session, production_log):
    """
    Calculate and accumulate costs for a work order based on production log.

    Implements incremental cost accumulation:
    - Material Cost: Proportional to quantity produced vs planned quantity
    - Labor Cost: Operation hours × work center cost per hour
    - Overhead Cost: 50% of labor cost (configurable overhead rate)
    - Total Cost: Sum of material, labor, and overhead costs

    Args:
        db: Database session
        production_log: Production log entry with quantity produced
    """
    # Fetch work order with eager loading
    work_order = db.query(WorkOrder).filter(
        WorkOrder.id == production_log.work_order_id
    ).first()

    if not work_order:
        logger.error(f"Work order {production_log.work_order_id} not found for production log {production_log.id}")
        return

    logger.info(f"Calculating costs for work order {work_order.work_order_number} (ID: {work_order.id})")

    # Convert quantities to Decimal for precise calculation
    quantity_produced = Decimal(str(production_log.quantity_produced))
    planned_quantity = Decimal(str(work_order.planned_quantity))

    if planned_quantity == 0:
        logger.warning(f"Work order {work_order.work_order_number} has zero planned_quantity, skipping cost calculation")
        return

    # Calculate production ratio (used for material cost allocation)
    production_ratio = quantity_produced / planned_quantity

    # ===========================
    # 1. MATERIAL COST CALCULATION
    # ===========================
    material_cost = Decimal("0.0")

    # Query work order materials with their costing information
    work_order_materials = db.query(
        WorkOrderMaterial,
        MaterialCosting
    ).join(
        MaterialCosting,
        MaterialCosting.material_id == WorkOrderMaterial.material_id
    ).filter(
        WorkOrderMaterial.work_order_id == work_order.id,
        MaterialCosting.organization_id == work_order.organization_id,
        MaterialCosting.plant_id == work_order.plant_id
    ).all()

    for wom, costing in work_order_materials:
        # Determine unit cost (prefer current_average_cost, fallback to standard_cost)
        unit_cost = costing.current_average_cost or costing.standard_cost or Decimal("0.0")

        # Calculate material cost: (quantity_produced / planned_quantity) × (material_quantity × unit_cost)
        planned_material_qty = Decimal(str(wom.planned_quantity))
        material_line_cost = production_ratio * planned_material_qty * unit_cost
        material_cost += material_line_cost

        logger.debug(
            f"Material {costing.material_id}: "
            f"planned_qty={planned_material_qty}, "
            f"unit_cost={unit_cost}, "
            f"line_cost={material_line_cost:.2f}"
        )

    # Handle case with no materials configured
    if not work_order_materials:
        logger.warning(f"No materials configured for work order {work_order.work_order_number}")

    # ===========================
    # 2. LABOR COST CALCULATION
    # ===========================
    labor_cost = Decimal("0.0")

    # Determine labor hours from production log or operation
    if production_log.operation_id:
        # Query the operation to get work center and time information
        operation = db.query(WorkOrderOperation, WorkCenter).join(
            WorkCenter,
            WorkCenter.id == WorkOrderOperation.work_center_id
        ).filter(
            WorkOrderOperation.id == production_log.operation_id
        ).first()

        if operation:
            op, work_center = operation

            # Calculate labor hours (convert minutes to hours)
            # Use actual times if available, otherwise use planned times
            setup_time_minutes = op.actual_setup_time or op.setup_time_minutes or 0.0
            run_time_minutes = op.actual_run_time or (op.run_time_per_unit_minutes * float(quantity_produced))

            total_hours = Decimal(str((setup_time_minutes + run_time_minutes) / 60.0))
            cost_per_hour = Decimal(str(work_center.cost_per_hour))

            # Calculate labor cost: hours × work_center.cost_per_hour
            labor_cost = total_hours * cost_per_hour

            logger.debug(
                f"Labor cost for operation {op.operation_number}: "
                f"setup_time={setup_time_minutes}min, "
                f"run_time={run_time_minutes}min, "
                f"total_hours={total_hours:.2f}h, "
                f"cost_per_hour={cost_per_hour}, "
                f"labor_cost={labor_cost:.2f}"
            )
        else:
            logger.warning(f"Operation {production_log.operation_id} not found for production log {production_log.id}")
    else:
        # No operation specified - use default estimation if available
        # Query all operations for the work order to estimate total labor
        operations = db.query(WorkOrderOperation, WorkCenter).join(
            WorkCenter,
            WorkCenter.id == WorkOrderOperation.work_center_id
        ).filter(
            WorkOrderOperation.work_order_id == work_order.id
        ).all()

        if operations:
            # Estimate labor cost proportional to production ratio
            for op, work_center in operations:
                setup_time_minutes = op.setup_time_minutes or 0.0
                run_time_per_unit = op.run_time_per_unit_minutes or 0.0

                # Calculate time for this production batch
                total_minutes = setup_time_minutes + (run_time_per_unit * float(quantity_produced))
                total_hours = Decimal(str(total_minutes / 60.0))
                cost_per_hour = Decimal(str(work_center.cost_per_hour))

                operation_labor_cost = total_hours * cost_per_hour
                labor_cost += operation_labor_cost

                logger.debug(
                    f"Estimated labor for operation {op.operation_number}: "
                    f"hours={total_hours:.2f}h, "
                    f"cost={operation_labor_cost:.2f}"
                )
        else:
            logger.warning(f"No operations configured for work order {work_order.work_order_number}")

    # ===========================
    # 3. OVERHEAD COST CALCULATION
    # ===========================
    # Overhead rate: 50% of labor cost (configurable in future)
    overhead_rate = Decimal("0.5")
    overhead_cost = labor_cost * overhead_rate

    logger.debug(f"Overhead cost (50% of labor): {overhead_cost:.2f}")

    # ===========================
    # 4. UPDATE WORK ORDER COSTS
    # ===========================
    # Accumulate costs incrementally (add to existing costs)
    work_order.actual_material_cost = float(Decimal(str(work_order.actual_material_cost)) + material_cost)
    work_order.actual_labor_cost = float(Decimal(str(work_order.actual_labor_cost)) + labor_cost)
    work_order.actual_overhead_cost = float(Decimal(str(work_order.actual_overhead_cost)) + overhead_cost)
    work_order.total_actual_cost = (
        work_order.actual_material_cost +
        work_order.actual_labor_cost +
        work_order.actual_overhead_cost
    )

    logger.info(
        f"Updated costs for work order {work_order.work_order_number}: "
        f"material=+{material_cost:.2f} (total={work_order.actual_material_cost:.2f}), "
        f"labor=+{labor_cost:.2f} (total={work_order.actual_labor_cost:.2f}), "
        f"overhead=+{overhead_cost:.2f} (total={work_order.actual_overhead_cost:.2f}), "
        f"total_cost={work_order.total_actual_cost:.2f}"
    )

    # Commit the cost updates
    db.commit()
    db.refresh(work_order)


@router.get("/work-order/{work_order_id}", response_model=ProductionLogListResponse)
def list_production_logs(
    work_order_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List production logs for a work order.

    Retrieve production logs with optional time-range filtering and pagination.

    Args:
        work_order_id: Work order ID
        start_time: Optional start time filter
        end_time: Optional end time filter
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
        db: Database session

    Returns:
        ProductionLogListResponse: Paginated production logs
    """
    repo = ProductionLogRepository(db)
    return repo.list_by_work_order(
        work_order_id=work_order_id,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )


@router.get("/work-order/{work_order_id}/summary", response_model=ProductionSummaryResponse)
def get_production_summary(work_order_id: int, db: Session = Depends(get_db)):
    """
    Get aggregated production statistics for a work order.

    Returns summary including total produced, scrapped, reworked, and yield rate.

    Args:
        work_order_id: Work order ID
        db: Database session

    Returns:
        ProductionSummaryResponse: Aggregated production statistics

    Raises:
        HTTPException: 404 if no production logs found
    """
    repo = ProductionLogRepository(db)
    summary = repo.get_summary(work_order_id)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No production logs found for work order {work_order_id}"
        )
    return summary


@router.get("/{log_id}", response_model=ProductionLogResponse)
def get_production_log(log_id: int, db: Session = Depends(get_db)):
    """
    Get single production log by ID.

    Args:
        log_id: Production log ID
        db: Database session

    Returns:
        ProductionLogResponse: Production log

    Raises:
        HTTPException: 404 if production log not found
    """
    repo = ProductionLogRepository(db)
    log = repo.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"Production log {log_id} not found")
    return log
