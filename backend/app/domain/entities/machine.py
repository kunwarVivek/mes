"""
Domain entities for Equipment & Machines module.
Pure Python classes representing business domain concepts.
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
import re
import enum


class MachineStatus(str, enum.Enum):
    """Machine status enum"""
    AVAILABLE = "AVAILABLE"
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    DOWN = "DOWN"
    SETUP = "SETUP"
    MAINTENANCE = "MAINTENANCE"


class MachineDomain:
    """Domain entity for Machine equipment"""

    MACHINE_CODE_PATTERN = re.compile(r'^[A-Z0-9]{1,20}$')

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        machine_code: str,
        machine_name: str,
        description: str,
        work_center_id: int,
        status: MachineStatus,
        is_active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._machine_code = machine_code.upper().strip()
        self._machine_name = machine_name
        self._description = description
        self._work_center_id = work_center_id
        self._status = status
        self._is_active = is_active
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate machine business rules"""
        if not self._machine_code:
            raise ValueError("Machine code cannot be empty")
        if len(self._machine_code) > 20:
            raise ValueError("Machine code cannot exceed 20 characters")
        if not self.MACHINE_CODE_PATTERN.match(self._machine_code):
            raise ValueError("Machine code must be alphanumeric")
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if not self._machine_name:
            raise ValueError("Machine name cannot be empty")
        if self._work_center_id <= 0:
            raise ValueError("Work center ID must be positive")

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
    def machine_code(self) -> str:
        return self._machine_code

    @property
    def machine_name(self) -> str:
        return self._machine_name

    @property
    def description(self) -> str:
        return self._description

    @property
    def work_center_id(self) -> int:
        return self._work_center_id

    @property
    def status(self) -> MachineStatus:
        return self._status

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def change_status(self, new_status: MachineStatus) -> None:
        """Business logic: Change machine status"""
        self._status = new_status

    def activate(self) -> None:
        """Business logic: Activate machine"""
        self._is_active = True

    def deactivate(self) -> None:
        """Business logic: Deactivate machine"""
        self._is_active = False

    def __repr__(self):
        return f"<Machine(code='{self._machine_code}', status='{self._status}', org={self._organization_id})>"


class MachineStatusHistoryDomain:
    """Domain entity for tracking machine status changes over time"""

    def __init__(
        self,
        id: Optional[int],
        machine_id: int,
        status: MachineStatus,
        started_at: datetime,
        ended_at: Optional[datetime] = None,
        notes: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._machine_id = machine_id
        self._status = status
        self._started_at = started_at
        self._ended_at = ended_at
        self._notes = notes
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate status history business rules"""
        if self._machine_id <= 0:
            raise ValueError("Machine ID must be positive")
        if self._ended_at is not None and self._ended_at < self._started_at:
            raise ValueError("End time cannot be before start time")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def machine_id(self) -> int:
        return self._machine_id

    @property
    def status(self) -> MachineStatus:
        return self._status

    @property
    def started_at(self) -> datetime:
        return self._started_at

    @property
    def ended_at(self) -> Optional[datetime]:
        return self._ended_at

    @property
    def notes(self) -> Optional[str]:
        return self._notes

    def get_duration_minutes(self) -> Optional[float]:
        """Calculate duration in minutes. Returns None if period is ongoing."""
        if self._ended_at is None:
            return None
        delta = self._ended_at - self._started_at
        return delta.total_seconds() / 60.0

    def end_period(self, ended_at: datetime) -> None:
        """Business logic: End the status period"""
        if ended_at < self._started_at:
            raise ValueError("End time cannot be before start time")
        self._ended_at = ended_at

    def __repr__(self):
        return f"<MachineStatusHistory(machine_id={self._machine_id}, status='{self._status}', duration={self.get_duration_minutes()})>"


@dataclass
class OEEMetrics:
    """Value object for OEE calculation results"""
    availability: float
    performance: float
    quality: float
    oee_score: float


class OEECalculator:
    """Service for calculating Overall Equipment Effectiveness (OEE)"""

    @staticmethod
    def calculate_oee(
        total_time_minutes: float,
        downtime_minutes: float,
        ideal_cycle_time: float,
        total_pieces: int,
        defect_pieces: int
    ) -> OEEMetrics:
        """
        Calculate OEE metrics.

        OEE = Availability × Performance × Quality

        Availability = (Total Time - Downtime) / Total Time
        Performance = (Ideal Cycle Time × Total Pieces) / Operating Time
        Quality = (Total Pieces - Defect Pieces) / Total Pieces

        Args:
            total_time_minutes: Total scheduled production time (minutes)
            downtime_minutes: Total downtime (breakdowns, maintenance, etc.)
            ideal_cycle_time: Ideal time to produce one piece (minutes)
            total_pieces: Total pieces produced (including defects)
            defect_pieces: Number of defective pieces

        Returns:
            OEEMetrics with availability, performance, quality, and overall OEE score

        Raises:
            ValueError: If inputs are invalid
        """
        # Validation
        if total_time_minutes <= 0:
            raise ValueError("Total time must be positive")
        if downtime_minutes < 0:
            raise ValueError("Downtime cannot be negative")
        if downtime_minutes > total_time_minutes:
            raise ValueError("Downtime cannot exceed total time")
        if ideal_cycle_time <= 0:
            raise ValueError("Ideal cycle time must be positive")
        if total_pieces < 0:
            raise ValueError("Total pieces cannot be negative")
        if defect_pieces < 0:
            raise ValueError("Defect pieces cannot be negative")
        if defect_pieces > total_pieces:
            raise ValueError("Defect pieces cannot exceed total pieces")

        # Calculate Availability
        operating_time = total_time_minutes - downtime_minutes
        availability = operating_time / total_time_minutes if total_time_minutes > 0 else 0.0

        # Calculate Performance
        if operating_time > 0:
            performance = (ideal_cycle_time * total_pieces) / operating_time
            # Cap performance at 1.0 (cannot be more than 100% of ideal)
            performance = min(performance, 1.0)
        else:
            performance = 0.0

        # Calculate Quality
        if total_pieces > 0:
            good_pieces = total_pieces - defect_pieces
            quality = good_pieces / total_pieces
        else:
            quality = 1.0  # No production = no defects

        # Calculate OEE
        oee_score = availability * performance * quality

        return OEEMetrics(
            availability=availability,
            performance=performance,
            quality=quality,
            oee_score=oee_score
        )
