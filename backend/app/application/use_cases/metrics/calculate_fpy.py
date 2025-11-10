"""
Calculate FPY Use Case

Calculates First Pass Yield (FPY) metrics.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.infrastructure.repositories.metrics_repository import MetricsRepository
from app.infrastructure.cache.cache_service import CacheService


class CalculateFPYDTO:
    """Data Transfer Object for FPY calculation request."""

    def __init__(
        self,
        plant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None,
        include_work_order_breakdown: bool = False,
        breakdown_limit: int = 10
    ):
        self.plant_id = plant_id
        self.start_date = start_date
        self.end_date = end_date
        self.organization_id = organization_id
        self.include_work_order_breakdown = include_work_order_breakdown
        self.breakdown_limit = breakdown_limit


class FPYResult:
    """Value object for FPY calculation result."""

    def __init__(
        self,
        total_inspected: int,
        total_passed: int,
        total_failed: int,
        fpy_percentage: float,
        defect_rate: float,
        start_date: datetime,
        end_date: datetime,
        work_order_breakdown: Optional[List[dict]] = None
    ):
        self.total_inspected = total_inspected
        self.total_passed = total_passed
        self.total_failed = total_failed
        self.fpy_percentage = fpy_percentage
        self.defect_rate = defect_rate
        self.start_date = start_date
        self.end_date = end_date
        self.work_order_breakdown = work_order_breakdown


class CalculateFPYUseCase:
    """
    Use case for calculating FPY (First Pass Yield).

    FPY Formula:
    - FPY = (Passed Quantity / Inspected Quantity) × 100%
    - Defect Rate = (Failed Quantity / Inspected Quantity) × 100%

    Business Rules:
    - BR-FPY-001: FPY > 99% is world-class, 95-99% is good, <95% needs improvement
    - BR-FPY-002: Only counts first-time inspections (from inspection_log table)
    - BR-FPY-003: Work order breakdown shows top 10 worst performers by default
    - BR-FPY-004: Results cached for 15 minutes (dashboard TTL)
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = MetricsRepository(db)
        self.cache = CacheService(db)

    def execute(self, dto: CalculateFPYDTO) -> FPYResult:
        """
        Execute FPY calculation.

        Args:
            dto: CalculateFPYDTO with filters and options

        Returns:
            FPYResult with first pass yield metrics

        Raises:
            ValidationException: If date range is invalid
        """
        # Validate date range
        if dto.start_date and dto.end_date and dto.start_date >= dto.end_date:
            from app.core.exceptions import ValidationException
            raise ValidationException(
                "Start date must be before end date",
                field="start_date"
            )

        # Set defaults
        start_date = dto.start_date or (datetime.now() - timedelta(days=30))
        end_date = dto.end_date or datetime.now()

        # Try cache first (BR-FPY-004)
        cache_key = self._generate_cache_key(dto, start_date, end_date)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return self._dict_to_result(cached_result)

        # Calculate FPY
        fpy_data = self.repo.get_fpy_data(
            plant_id=dto.plant_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=dto.organization_id
        )

        # Get work order breakdown if requested (BR-FPY-003)
        work_order_breakdown = None
        if dto.include_work_order_breakdown:
            work_order_breakdown = self.repo.get_fpy_by_work_order(
                plant_id=dto.plant_id,
                start_date=start_date,
                end_date=end_date,
                organization_id=dto.organization_id,
                limit=dto.breakdown_limit
            )

        result = FPYResult(
            total_inspected=fpy_data["total_inspected"],
            total_passed=fpy_data["total_passed"],
            total_failed=fpy_data["total_failed"],
            fpy_percentage=fpy_data["fpy_percentage"],
            defect_rate=fpy_data["defect_rate"],
            start_date=start_date,
            end_date=end_date,
            work_order_breakdown=work_order_breakdown
        )

        # Cache result for 15 minutes
        self.cache.set(cache_key, self._result_to_dict(result), ttl=900)

        return result

    def _generate_cache_key(
        self,
        dto: CalculateFPYDTO,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Generate cache key for FPY result."""
        return (
            f"fpy_org{dto.organization_id}_plant{dto.plant_id}_"
            f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_"
            f"breakdown{dto.include_work_order_breakdown}_"
            f"limit{dto.breakdown_limit}"
        )

    def _result_to_dict(self, result: FPYResult) -> dict:
        """Convert FPYResult to dict for caching."""
        return {
            "total_inspected": result.total_inspected,
            "total_passed": result.total_passed,
            "total_failed": result.total_failed,
            "fpy_percentage": result.fpy_percentage,
            "defect_rate": result.defect_rate,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "work_order_breakdown": result.work_order_breakdown
        }

    def _dict_to_result(self, data: dict) -> FPYResult:
        """Convert dict to FPYResult from cache."""
        return FPYResult(
            total_inspected=data["total_inspected"],
            total_passed=data["total_passed"],
            total_failed=data["total_failed"],
            fpy_percentage=data["fpy_percentage"],
            defect_rate=data["defect_rate"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            work_order_breakdown=data.get("work_order_breakdown")
        )
