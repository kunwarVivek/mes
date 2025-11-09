"""
Domain entities for Shift Management.
Pure Python classes representing business domain concepts for shift operations.
"""
from datetime import datetime, time, timedelta
from typing import Optional


class ShiftDomain:
    """Domain entity for Shift with business logic"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        shift_name: str,
        shift_code: str,
        start_time: time,
        end_time: time,
        production_target: float,
        is_active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._shift_name = shift_name.strip()
        self._shift_code = shift_code.upper().strip()
        self._start_time = start_time
        self._end_time = end_time
        self._production_target = production_target
        self._is_active = is_active
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate shift business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if not self._shift_name:
            raise ValueError("Shift name cannot be empty")
        if not self._shift_code:
            raise ValueError("Shift code cannot be empty")
        if self._production_target < 0:
            raise ValueError("Production target cannot be negative")

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
    def shift_name(self) -> str:
        return self._shift_name

    @property
    def shift_code(self) -> str:
        return self._shift_code

    @property
    def start_time(self) -> time:
        return self._start_time

    @property
    def end_time(self) -> time:
        return self._end_time

    @property
    def production_target(self) -> float:
        return self._production_target

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def activate(self) -> None:
        """Business logic: Activate shift"""
        self._is_active = True

    def deactivate(self) -> None:
        """Business logic: Deactivate shift"""
        self._is_active = False

    def calculate_duration_hours(self) -> float:
        """Calculate shift duration in hours, handling overnight shifts"""
        start_dt = datetime.combine(datetime.today(), self._start_time)
        end_dt = datetime.combine(datetime.today(), self._end_time)

        # Handle overnight shifts (end_time < start_time)
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        duration = end_dt - start_dt
        return duration.total_seconds() / 3600

    def __repr__(self):
        return f"<Shift(code='{self._shift_code}', name='{self._shift_name}')>"


class ShiftHandoverDomain:
    """Domain entity for Shift Handover with business logic"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        from_shift_id: int,
        to_shift_id: int,
        handover_date: datetime,
        wip_quantity: float,
        production_summary: str,
        handover_by_user_id: int,
        quality_issues: Optional[str] = None,
        machine_status: Optional[str] = None,
        material_status: Optional[str] = None,
        safety_incidents: Optional[str] = None,
        acknowledged_by_user_id: Optional[int] = None,
        acknowledged_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._from_shift_id = from_shift_id
        self._to_shift_id = to_shift_id
        self._handover_date = handover_date
        self._wip_quantity = wip_quantity
        self._production_summary = production_summary
        self._quality_issues = quality_issues
        self._machine_status = machine_status
        self._material_status = material_status
        self._safety_incidents = safety_incidents
        self._handover_by_user_id = handover_by_user_id
        self._acknowledged_by_user_id = acknowledged_by_user_id
        self._acknowledged_at = acknowledged_at
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate shift handover business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if self._from_shift_id == self._to_shift_id:
            raise ValueError("Cannot handover to the same shift")
        if self._wip_quantity < 0:
            raise ValueError("WIP quantity cannot be negative")
        if self._handover_by_user_id <= 0:
            raise ValueError("Handover by user ID must be positive")

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
    def from_shift_id(self) -> int:
        return self._from_shift_id

    @property
    def to_shift_id(self) -> int:
        return self._to_shift_id

    @property
    def handover_date(self) -> datetime:
        return self._handover_date

    @property
    def wip_quantity(self) -> float:
        return self._wip_quantity

    @property
    def production_summary(self) -> str:
        return self._production_summary

    @property
    def quality_issues(self) -> Optional[str]:
        return self._quality_issues

    @property
    def machine_status(self) -> Optional[str]:
        return self._machine_status

    @property
    def material_status(self) -> Optional[str]:
        return self._material_status

    @property
    def safety_incidents(self) -> Optional[str]:
        return self._safety_incidents

    @property
    def handover_by_user_id(self) -> int:
        return self._handover_by_user_id

    @property
    def acknowledged_by_user_id(self) -> Optional[int]:
        return self._acknowledged_by_user_id

    @property
    def acknowledged_at(self) -> Optional[datetime]:
        return self._acknowledged_at

    @property
    def is_acknowledged(self) -> bool:
        """Check if handover has been acknowledged"""
        return self._acknowledged_by_user_id is not None

    def acknowledge(self, user_id: int) -> None:
        """Business logic: Acknowledge shift handover"""
        if self.is_acknowledged:
            raise ValueError("Handover already acknowledged")
        if user_id <= 0:
            raise ValueError("User ID must be positive")

        self._acknowledged_by_user_id = user_id
        self._acknowledged_at = datetime.utcnow()

    def __repr__(self):
        return f"<ShiftHandover(from={self._from_shift_id}, to={self._to_shift_id}, date={self._handover_date})>"
