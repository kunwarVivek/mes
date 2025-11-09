"""
Production Logs API Router.

RESTful endpoints for production logging.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.application.dtos.production_log_dto import (
    ProductionLogCreateRequest,
    ProductionLogResponse,
    ProductionLogListResponse,
    ProductionSummaryResponse
)
from app.infrastructure.repositories.production_log_repository import ProductionLogRepository


router = APIRouter()


@router.post("/", response_model=ProductionLogResponse, status_code=201)
def log_production(dto: ProductionLogCreateRequest, db: Session = Depends(get_db)):
    """
    Log new production entry.

    Creates a new production log entry for a work order.

    Args:
        dto: Production log create request
        db: Database session

    Returns:
        ProductionLogResponse: Created production log
    """
    repo = ProductionLogRepository(db)
    log = repo.create(dto)
    return log


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
