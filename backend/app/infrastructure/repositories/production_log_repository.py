"""
Production Log Repository.

Handles database operations for production logs with TimescaleDB optimizations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.models.production_log import ProductionLog
from app.application.dtos.production_log_dto import (
    ProductionLogCreateRequest,
    ProductionSummaryResponse
)


class ProductionLogRepository:
    """Repository for production log database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: ProductionLogCreateRequest) -> ProductionLog:
        """
        Log new production entry.

        Args:
            dto: Production log create request

        Returns:
            ProductionLog: Created production log
        """
        log = ProductionLog(**dto.model_dump())
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_by_id(self, log_id: int) -> Optional[ProductionLog]:
        """
        Get single production log by ID.

        Args:
            log_id: Production log ID

        Returns:
            Optional[ProductionLog]: Production log if found
        """
        return self.db.query(ProductionLog).filter(ProductionLog.id == log_id).first()

    def list_by_work_order(
        self,
        work_order_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        List production logs for a work order with time filtering.

        Utilizes TimescaleDB hypertable for efficient time-range queries.

        Args:
            work_order_id: Work order ID
            start_time: Optional start time filter
            end_time: Optional end time filter
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with items, total, page, page_size
        """
        query = self.db.query(ProductionLog).filter(ProductionLog.work_order_id == work_order_id)

        if start_time:
            query = query.filter(ProductionLog.timestamp >= start_time)

        if end_time:
            query = query.filter(ProductionLog.timestamp <= end_time)

        # Order by timestamp descending (most recent first)
        query = query.order_by(ProductionLog.timestamp.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_summary(self, work_order_id: int) -> Optional[ProductionSummaryResponse]:
        """
        Get aggregated production statistics for a work order.

        Performs efficient aggregation using database-level queries.

        Args:
            work_order_id: Work order ID

        Returns:
            Optional[ProductionSummaryResponse]: Aggregated statistics or None if no logs
        """
        result = self.db.query(
            func.sum(ProductionLog.quantity_produced).label('total_produced'),
            func.sum(ProductionLog.quantity_scrapped).label('total_scrapped'),
            func.sum(ProductionLog.quantity_reworked).label('total_reworked'),
            func.count(ProductionLog.id).label('log_count'),
            func.min(ProductionLog.timestamp).label('first_log'),
            func.max(ProductionLog.timestamp).label('last_log'),
        ).filter(ProductionLog.work_order_id == work_order_id).first()

        if not result or result.log_count == 0:
            return None

        total_produced = result.total_produced or Decimal("0")
        total_scrapped = result.total_scrapped or Decimal("0")
        total_reworked = result.total_reworked or Decimal("0")
        total = total_produced + total_scrapped + total_reworked

        yield_rate = (total_produced / total * 100) if total > 0 else Decimal("0")

        return ProductionSummaryResponse(
            work_order_id=work_order_id,
            total_produced=total_produced,
            total_scrapped=total_scrapped,
            total_reworked=total_reworked,
            yield_rate=yield_rate.quantize(Decimal("0.01")),
            log_count=result.log_count,
            first_log=result.first_log,
            last_log=result.last_log
        )
