"""
Lane domain entities for production scheduling
"""
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from enum import Enum


class LaneAssignmentStatus(str, Enum):
    """Status of lane assignment"""
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass
class LaneDomain:
    """Lane entity - Physical production line/area"""
    id: int
    plant_id: int
    lane_code: str
    lane_name: str
    capacity_per_day: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate lane data"""
        if not self.lane_code or len(self.lane_code) > 50:
            raise ValueError("lane_code must be 1-50 characters")

        if not self.lane_name or len(self.lane_name) > 200:
            raise ValueError("lane_name must be 1-200 characters")

        if self.capacity_per_day <= 0:
            raise ValueError("capacity_per_day must be positive")


@dataclass
class LaneAssignmentDomain:
    """Lane Assignment entity - Scheduled work on lanes"""
    id: int
    organization_id: int
    plant_id: int
    lane_id: int
    work_order_id: int
    project_id: Optional[int]
    scheduled_start: date
    scheduled_end: date
    allocated_capacity: Decimal
    priority: int
    status: LaneAssignmentStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate assignment data"""
        if self.scheduled_end < self.scheduled_start:
            raise ValueError("scheduled_end must be >= scheduled_start")

        if self.allocated_capacity <= 0:
            raise ValueError("allocated_capacity must be positive")

    @property
    def duration_days(self) -> int:
        """Calculate duration in days"""
        return (self.scheduled_end - self.scheduled_start).days + 1

    @property
    def total_capacity_needed(self) -> Decimal:
        """Calculate total capacity needed for the assignment"""
        return self.allocated_capacity * self.duration_days
