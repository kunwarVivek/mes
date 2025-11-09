"""
Project Domain Entity - Multi-project manufacturing.

Business logic and validation for manufacturing projects.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from enum import Enum


class ProjectStatus(str, Enum):
    """Project lifecycle status"""
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass
class ProjectDomain:
    """
    Project entity - Multi-project manufacturing.

    Represents a discrete manufacturing project with BOM linkage,
    timeline tracking, and status management.
    """
    id: int
    organization_id: int
    plant_id: int
    project_code: str
    project_name: str
    description: Optional[str]
    bom_id: Optional[int]
    planned_start_date: Optional[date]
    planned_end_date: Optional[date]
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]
    status: ProjectStatus
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate project data"""
        if not self.project_code or len(self.project_code) > 50:
            raise ValueError("project_code must be 1-50 characters")

        if not self.project_name or len(self.project_name) > 200:
            raise ValueError("project_name must be 1-200 characters")

        if self.planned_start_date and self.planned_end_date:
            if self.planned_end_date < self.planned_start_date:
                raise ValueError("planned_end_date must be >= planned_start_date")
