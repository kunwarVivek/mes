"""
Calculate OEE Use Case

Calculates Overall Equipment Effectiveness (OEE) metrics.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.infrastructure.repositories.metrics_repository import MetricsRepository
from app.infrastructure.cache.cache_service import CacheService


class CalculateOEEDTO:
    """Data Transfer Object for OEE calculation request."""

    def __init__(
        self,
        plant_id: Optional[int] = None,
        machine_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None,
        by_machine: bool = False
    ):
        self.plant_id = plant_id
        self.machine_id = machine_id
        self.start_date = start_date
        self.end_date = end_date
        self.organization_id = organization_id
        self.by_machine = by_machine


class OEEResult:
    """Value object for OEE calculation result."""

    def __init__(
        self,
        total_time_minutes: float,
        downtime_minutes: float,
        operating_time_minutes: float,
        total_pieces: int,
        good_pieces: int,
        defect_pieces: int,
        scrapped_pieces: int,
        reworked_pieces: int,
        availability: float,
        performance: float,
        quality: float,
        oee: float,
        start_date: datetime,
        end_date: datetime,
        machine_breakdown: Optional[List[dict]] = None
    ):
        self.total_time_minutes = total_time_minutes
        self.downtime_minutes = downtime_minutes
        self.operating_time_minutes = operating_time_minutes
        self.total_pieces = total_pieces
        self.good_pieces = good_pieces
        self.defect_pieces = defect_pieces
        self.scrapped_pieces = scrapped_pieces
        self.reworked_pieces = reworked_pieces
        self.availability = availability
        self.performance = performance
        self.quality = quality
        self.oee = oee
        self.start_date = start_date
        self.end_date = end_date
        self.machine_breakdown = machine_breakdown


class CalculateOEEUseCase:
    """
    Use case for calculating OEE (Overall Equipment Effectiveness).

    OEE Formula:
    - OEE = Availability × Performance × Quality
    - Availability = (Total Time - Downtime) / Total Time
    - Performance = (Ideal Cycle Time × Total Pieces) / Operating Time
    - Quality = Good Pieces / Total Pieces

    Business Rules:
    - BR-OEE-001: OEE < 60% is poor, 60-85% is fair, >85% is world-class
    - BR-OEE-002: Downtime includes machine DOWN and MAINTENANCE status
    - BR-OEE-003: Good pieces = Total produced - Scrapped (reworked is counted as good)
    - BR-OEE-004: Results cached for 15 minutes (dashboard TTL)
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = MetricsRepository(db)
        self.cache = CacheService(db)

    def execute(self, dto: CalculateOEEDTO) -> OEEResult:
        """
        Execute OEE calculation.

        Args:
            dto: CalculateOEEDTO with filters and options

        Returns:
            OEEResult with OEE components and metrics

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

        # Try cache first (BR-OEE-004)
        cache_key = self._generate_cache_key(dto, start_date, end_date)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return self._dict_to_result(cached_result)

        # Calculate OEE
        if dto.by_machine:
            # Get breakdown by machine
            machine_data = self.repo.get_oee_by_machine(
                plant_id=dto.plant_id,
                start_date=start_date,
                end_date=end_date,
                organization_id=dto.organization_id
            )

            # Aggregate totals
            aggregate_data = self._aggregate_machine_data(machine_data)
            result = OEEResult(
                total_time_minutes=aggregate_data["total_time_minutes"],
                downtime_minutes=aggregate_data["downtime_minutes"],
                operating_time_minutes=aggregate_data["operating_time_minutes"],
                total_pieces=aggregate_data["total_pieces"],
                good_pieces=aggregate_data["good_pieces"],
                defect_pieces=aggregate_data["defect_pieces"],
                scrapped_pieces=aggregate_data["scrapped_pieces"],
                reworked_pieces=aggregate_data["reworked_pieces"],
                availability=aggregate_data["availability"],
                performance=aggregate_data["performance"],
                quality=aggregate_data["quality"],
                oee=aggregate_data["oee"],
                start_date=start_date,
                end_date=end_date,
                machine_breakdown=machine_data
            )
        else:
            # Get overall OEE
            oee_data = self.repo.get_oee_data(
                plant_id=dto.plant_id,
                machine_id=dto.machine_id,
                start_date=start_date,
                end_date=end_date,
                organization_id=dto.organization_id
            )

            result = OEEResult(
                total_time_minutes=oee_data["total_time_minutes"],
                downtime_minutes=oee_data["downtime_minutes"],
                operating_time_minutes=oee_data["operating_time_minutes"],
                total_pieces=oee_data["total_pieces"],
                good_pieces=oee_data["good_pieces"],
                defect_pieces=oee_data["defect_pieces"],
                scrapped_pieces=oee_data["scrapped_pieces"],
                reworked_pieces=oee_data["reworked_pieces"],
                availability=oee_data["availability"],
                performance=oee_data["performance"],
                quality=oee_data["quality"],
                oee=oee_data["oee"],
                start_date=start_date,
                end_date=end_date,
                machine_breakdown=None
            )

        # Cache result for 15 minutes
        self.cache.set(cache_key, self._result_to_dict(result), ttl=900)

        return result

    def _generate_cache_key(
        self,
        dto: CalculateOEEDTO,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Generate cache key for OEE result."""
        return (
            f"oee_org{dto.organization_id}_plant{dto.plant_id}_"
            f"machine{dto.machine_id}_"
            f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_"
            f"by_machine{dto.by_machine}"
        )

    def _aggregate_machine_data(self, machine_data: List[dict]) -> dict:
        """Aggregate OEE data across multiple machines."""
        if not machine_data:
            return {
                "total_time_minutes": 0,
                "downtime_minutes": 0,
                "operating_time_minutes": 0,
                "total_pieces": 0,
                "good_pieces": 0,
                "defect_pieces": 0,
                "scrapped_pieces": 0,
                "reworked_pieces": 0,
                "availability": 0.0,
                "performance": 0.0,
                "quality": 0.0,
                "oee": 0.0
            }

        total_time = sum(m["total_time_minutes"] for m in machine_data)
        downtime = sum(m["downtime_minutes"] for m in machine_data)
        operating_time = total_time - downtime
        total_pieces = sum(m["total_pieces"] for m in machine_data)
        good_pieces = sum(m["good_pieces"] for m in machine_data)
        defect_pieces = sum(m["defect_pieces"] for m in machine_data)
        scrapped_pieces = sum(m["scrapped_pieces"] for m in machine_data)
        reworked_pieces = sum(m["reworked_pieces"] for m in machine_data)

        # Recalculate percentages
        availability = (operating_time / total_time * 100) if total_time > 0 else 0.0
        performance = 100.0 if total_pieces > 0 else 0.0  # Simplified
        quality = (good_pieces / total_pieces * 100) if total_pieces > 0 else 0.0
        oee = availability * performance * quality / 10000  # Divide by 10000 since percentages

        return {
            "total_time_minutes": total_time,
            "downtime_minutes": downtime,
            "operating_time_minutes": operating_time,
            "total_pieces": total_pieces,
            "good_pieces": good_pieces,
            "defect_pieces": defect_pieces,
            "scrapped_pieces": scrapped_pieces,
            "reworked_pieces": reworked_pieces,
            "availability": round(availability, 2),
            "performance": round(performance, 2),
            "quality": round(quality, 2),
            "oee": round(oee, 2)
        }

    def _result_to_dict(self, result: OEEResult) -> dict:
        """Convert OEEResult to dict for caching."""
        return {
            "total_time_minutes": result.total_time_minutes,
            "downtime_minutes": result.downtime_minutes,
            "operating_time_minutes": result.operating_time_minutes,
            "total_pieces": result.total_pieces,
            "good_pieces": result.good_pieces,
            "defect_pieces": result.defect_pieces,
            "scrapped_pieces": result.scrapped_pieces,
            "reworked_pieces": result.reworked_pieces,
            "availability": result.availability,
            "performance": result.performance,
            "quality": result.quality,
            "oee": result.oee,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "machine_breakdown": result.machine_breakdown
        }

    def _dict_to_result(self, data: dict) -> OEEResult:
        """Convert dict to OEEResult from cache."""
        return OEEResult(
            total_time_minutes=data["total_time_minutes"],
            downtime_minutes=data["downtime_minutes"],
            operating_time_minutes=data["operating_time_minutes"],
            total_pieces=data["total_pieces"],
            good_pieces=data["good_pieces"],
            defect_pieces=data["defect_pieces"],
            scrapped_pieces=data["scrapped_pieces"],
            reworked_pieces=data["reworked_pieces"],
            availability=data["availability"],
            performance=data["performance"],
            quality=data["quality"],
            oee=data["oee"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            machine_breakdown=data.get("machine_breakdown")
        )
