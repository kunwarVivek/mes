"""
Calculate OTD Use Case

Calculates On-Time Delivery (OTD) metrics.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.infrastructure.repositories.metrics_repository import MetricsRepository
from app.infrastructure.cache.cache_service import CacheService


class CalculateOTDDTO:
    """Data Transfer Object for OTD calculation request."""

    def __init__(
        self,
        plant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None
    ):
        self.plant_id = plant_id
        self.start_date = start_date
        self.end_date = end_date
        self.organization_id = organization_id


class OTDResult:
    """Value object for OTD calculation result."""

    def __init__(
        self,
        total_completed: int,
        on_time: int,
        late: int,
        otd_percentage: float,
        average_delay_days: float,
        start_date: datetime,
        end_date: datetime
    ):
        self.total_completed = total_completed
        self.on_time = on_time
        self.late = late
        self.otd_percentage = otd_percentage
        self.average_delay_days = average_delay_days
        self.start_date = start_date
        self.end_date = end_date


class CalculateOTDUseCase:
    """
    Use case for calculating OTD (On-Time Delivery).

    OTD Formula:
    - OTD = (Work Orders Completed On-Time / Total Completed Work Orders) × 100%

    Business Rules:
    - BR-OTD-001: Work order is on-time if end_date_actual <= end_date_planned
    - BR-OTD-002: If end_date_actual is NULL but status is COMPLETED, assume on-time
    - BR-OTD-003: OTD > 95% is excellent, 85-95% is good, <85% needs improvement
    - BR-OTD-004: Results cached for 15 minutes (dashboard TTL)
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = MetricsRepository(db)
        self.cache = CacheService(db)

    def execute(self, dto: CalculateOTDDTO) -> OTDResult:
        """
        Execute OTD calculation.

        Args:
            dto: CalculateOTDDTO with filters

        Returns:
            OTDResult with on-time delivery metrics

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

        # Try cache first (BR-OTD-004)
        cache_key = self._generate_cache_key(dto, start_date, end_date)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return self._dict_to_result(cached_result)

        # Calculate OTD
        otd_data = self.repo.get_otd_data(
            plant_id=dto.plant_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=dto.organization_id
        )

        result = OTDResult(
            total_completed=otd_data["total_completed"],
            on_time=otd_data["on_time"],
            late=otd_data["late"],
            otd_percentage=otd_data["otd_percentage"],
            average_delay_days=otd_data["average_delay_days"],
            start_date=start_date,
            end_date=end_date
        )

        # Cache result for 15 minutes
        self.cache.set(cache_key, self._result_to_dict(result), ttl=900)

        return result

    def _generate_cache_key(
        self,
        dto: CalculateOTDDTO,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Generate cache key for OTD result."""
        return (
            f"otd_org{dto.organization_id}_plant{dto.plant_id}_"
            f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        )

    def _result_to_dict(self, result: OTDResult) -> dict:
        """Convert OTDResult to dict for caching."""
        return {
            "total_completed": result.total_completed,
            "on_time": result.on_time,
            "late": result.late,
            "otd_percentage": result.otd_percentage,
            "average_delay_days": result.average_delay_days,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat()
        }

    def _dict_to_result(self, data: dict) -> OTDResult:
        """Convert dict to OTDResult from cache."""
        return OTDResult(
            total_completed=data["total_completed"],
            on_time=data["on_time"],
            late=data["late"],
            otd_percentage=data["otd_percentage"],
            average_delay_days=data["average_delay_days"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"])
        )
