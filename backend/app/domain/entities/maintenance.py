"""
Domain entities for Maintenance Management module.
Pure Python classes representing business domain concepts.
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
import enum


class TriggerType(str, enum.Enum):
    """PM schedule trigger type enum"""
    CALENDAR = "CALENDAR"
    METER = "METER"


class PMStatus(str, enum.Enum):
    """PM work order status enum"""
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DowntimeCategory(str, enum.Enum):
    """Downtime event category enum"""
    BREAKDOWN = "BREAKDOWN"
    PLANNED_MAINTENANCE = "PLANNED_MAINTENANCE"
    CHANGEOVER = "CHANGEOVER"
    NO_OPERATOR = "NO_OPERATOR"
    MATERIAL_SHORTAGE = "MATERIAL_SHORTAGE"


class PMScheduleDomain:
    """Domain entity for Preventive Maintenance Schedule"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        schedule_code: str,
        schedule_name: str,
        machine_id: int,
        trigger_type: TriggerType,
        frequency_days: Optional[int] = None,
        meter_threshold: Optional[float] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._schedule_code = schedule_code.upper().strip() if schedule_code else ""
        self._schedule_name = schedule_name
        self._machine_id = machine_id
        self._trigger_type = trigger_type
        self._frequency_days = frequency_days
        self._meter_threshold = meter_threshold
        self._is_active = is_active
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate PM schedule business rules"""
        if not self._schedule_code:
            raise ValueError("Schedule code cannot be empty")
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if self._machine_id <= 0:
            raise ValueError("Machine ID must be positive")

        # Validate trigger type requirements
        if self._trigger_type == TriggerType.CALENDAR:
            if self._frequency_days is None:
                raise ValueError("Calendar-based schedules require frequency_days")
            if self._frequency_days <= 0:
                raise ValueError("Frequency days must be positive")

        if self._trigger_type == TriggerType.METER:
            if self._meter_threshold is None:
                raise ValueError("Meter-based schedules require meter_threshold")
            if self._meter_threshold <= 0:
                raise ValueError("Meter threshold must be positive")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def organization_id(self) -> int:
        return self._organization_id

    @property
    def plant_id(self) -> int:
        return self._plant_id

    @property
    def schedule_code(self) -> str:
        return self._schedule_code

    @property
    def schedule_name(self) -> str:
        return self._schedule_name

    @property
    def machine_id(self) -> int:
        return self._machine_id

    @property
    def trigger_type(self) -> TriggerType:
        return self._trigger_type

    @property
    def frequency_days(self) -> Optional[int]:
        return self._frequency_days

    @property
    def meter_threshold(self) -> Optional[float]:
        return self._meter_threshold

    @property
    def is_active(self) -> bool:
        return self._is_active

    def activate(self) -> None:
        """Business logic: Activate PM schedule"""
        self._is_active = True

    def deactivate(self) -> None:
        """Business logic: Deactivate PM schedule"""
        self._is_active = False

    def __repr__(self):
        return f"<PMSchedule(code='{self._schedule_code}', type='{self._trigger_type}', org={self._organization_id})>"


class PMWorkOrderDomain:
    """Domain entity for PM Work Order"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        pm_schedule_id: int,
        machine_id: int,
        pm_number: str,
        status: PMStatus,
        scheduled_date: datetime,
        due_date: datetime,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        notes: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._pm_schedule_id = pm_schedule_id
        self._machine_id = machine_id
        self._pm_number = pm_number.upper().strip() if pm_number else ""
        self._status = status
        self._scheduled_date = scheduled_date
        self._due_date = due_date
        self._started_at = started_at
        self._completed_at = completed_at
        self._notes = notes
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate PM work order business rules"""
        if not self._pm_number:
            raise ValueError("PM number cannot be empty")
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if self._pm_schedule_id <= 0:
            raise ValueError("PM schedule ID must be positive")
        if self._machine_id <= 0:
            raise ValueError("Machine ID must be positive")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def organization_id(self) -> int:
        return self._organization_id

    @property
    def plant_id(self) -> int:
        return self._plant_id

    @property
    def pm_schedule_id(self) -> int:
        return self._pm_schedule_id

    @property
    def machine_id(self) -> int:
        return self._machine_id

    @property
    def pm_number(self) -> str:
        return self._pm_number

    @property
    def status(self) -> PMStatus:
        return self._status

    @property
    def scheduled_date(self) -> datetime:
        return self._scheduled_date

    @property
    def due_date(self) -> datetime:
        return self._due_date

    @property
    def started_at(self) -> Optional[datetime]:
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        return self._completed_at

    def start(self) -> None:
        """Business logic: Start PM work order (SCHEDULED -> IN_PROGRESS)"""
        if self._status != PMStatus.SCHEDULED:
            raise ValueError("PM work order can only be started from SCHEDULED status")
        self._status = PMStatus.IN_PROGRESS
        self._started_at = datetime.utcnow()

    def complete(self) -> None:
        """Business logic: Complete PM work order (IN_PROGRESS -> COMPLETED)"""
        if self._status != PMStatus.IN_PROGRESS:
            raise ValueError("PM work order can only be completed from IN_PROGRESS status")
        self._status = PMStatus.COMPLETED
        self._completed_at = datetime.utcnow()

    def cancel(self) -> None:
        """Business logic: Cancel PM work order"""
        if self._status == PMStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed PM work order")
        self._status = PMStatus.CANCELLED

    def __repr__(self):
        return f"<PMWorkOrder(number='{self._pm_number}', status='{self._status}', org={self._organization_id})>"


class DowntimeEventDomain:
    """Domain entity for equipment downtime tracking"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        machine_id: int,
        category: DowntimeCategory,
        reason: str,
        started_at: datetime,
        ended_at: Optional[datetime] = None,
        notes: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._machine_id = machine_id
        self._category = category
        self._reason = reason
        self._started_at = started_at
        self._ended_at = ended_at
        self._notes = notes
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate downtime event business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if self._machine_id <= 0:
            raise ValueError("Machine ID must be positive")
        if not self._reason:
            raise ValueError("Reason cannot be empty")
        if self._ended_at is not None and self._ended_at < self._started_at:
            raise ValueError("End time cannot be before start time")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def organization_id(self) -> int:
        return self._organization_id

    @property
    def plant_id(self) -> int:
        return self._plant_id

    @property
    def machine_id(self) -> int:
        return self._machine_id

    @property
    def category(self) -> DowntimeCategory:
        return self._category

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def started_at(self) -> datetime:
        return self._started_at

    @property
    def ended_at(self) -> Optional[datetime]:
        return self._ended_at

    def get_duration_minutes(self) -> Optional[float]:
        """Calculate downtime duration in minutes. Returns None if ongoing."""
        if self._ended_at is None:
            return None
        delta = self._ended_at - self._started_at
        return delta.total_seconds() / 60.0

    def end_event(self, ended_at: datetime) -> None:
        """Business logic: End the downtime event"""
        if ended_at < self._started_at:
            raise ValueError("End time cannot be before start time")
        self._ended_at = ended_at

    def __repr__(self):
        duration = self.get_duration_minutes()
        return f"<DowntimeEvent(machine_id={self._machine_id}, category='{self._category}', duration={duration})>"


@dataclass
class MTBFMTTRMetrics:
    """Value object for MTBF/MTTR calculation results"""
    mtbf: float  # Mean Time Between Failures (minutes)
    mttr: float  # Mean Time To Repair (minutes)
    availability: float  # System availability (0-1)


class MTBFMTTRCalculator:
    """Service for calculating MTBF and MTTR metrics"""

    @staticmethod
    def calculate_mtbf(
        total_operating_time: float,
        number_of_failures: int
    ) -> float:
        """
        Calculate Mean Time Between Failures (MTBF).

        MTBF = Total Operating Time / Number of Failures

        Args:
            total_operating_time: Total time equipment was operational (minutes)
            number_of_failures: Number of breakdowns/failures

        Returns:
            MTBF in minutes

        Raises:
            ValueError: If inputs are invalid
        """
        if total_operating_time <= 0:
            raise ValueError("Total operating time must be positive")
        if number_of_failures < 0:
            raise ValueError("Number of failures cannot be negative")
        if number_of_failures == 0:
            return float('inf')  # No failures = infinite MTBF

        return total_operating_time / number_of_failures

    @staticmethod
    def calculate_mttr(
        total_repair_time: float,
        number_of_failures: int
    ) -> float:
        """
        Calculate Mean Time To Repair (MTTR).

        MTTR = Total Repair Time / Number of Failures

        Args:
            total_repair_time: Total time spent on repairs (minutes)
            number_of_failures: Number of breakdowns/failures

        Returns:
            MTTR in minutes

        Raises:
            ValueError: If inputs are invalid
        """
        if total_repair_time < 0:
            raise ValueError("Total repair time cannot be negative")
        if number_of_failures < 0:
            raise ValueError("Number of failures cannot be negative")
        if number_of_failures == 0:
            return 0.0  # No failures = no repair time

        return total_repair_time / number_of_failures

    @staticmethod
    def calculate_metrics(
        total_operating_time: float,
        total_repair_time: float,
        number_of_failures: int
    ) -> MTBFMTTRMetrics:
        """
        Calculate complete MTBF/MTTR metrics including availability.

        Availability = MTBF / (MTBF + MTTR)

        Args:
            total_operating_time: Total time equipment was operational (minutes)
            total_repair_time: Total time spent on repairs (minutes)
            number_of_failures: Number of breakdowns/failures

        Returns:
            MTBFMTTRMetrics with MTBF, MTTR, and availability

        Raises:
            ValueError: If inputs are invalid
        """
        mtbf = MTBFMTTRCalculator.calculate_mtbf(total_operating_time, number_of_failures)
        mttr = MTBFMTTRCalculator.calculate_mttr(total_repair_time, number_of_failures)

        # Calculate availability
        if number_of_failures == 0:
            availability = 1.0  # Perfect availability
        else:
            availability = mtbf / (mtbf + mttr)

        return MTBFMTTRMetrics(
            mtbf=mtbf,
            mttr=mttr,
            availability=availability
        )
