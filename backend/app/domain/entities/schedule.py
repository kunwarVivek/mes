"""
Schedule domain entity - container for scheduled operations.
Phase 3: Production Planning Module - Component 6
"""
from datetime import datetime
from typing import List, Dict, Optional


class Schedule:
    """
    Schedule domain entity representing a production schedule.

    Contains scheduled operations with time slots on work centers.
    Supports status transitions: DRAFT -> PUBLISHED -> ACTIVE
    """

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        schedule_number: str,
        schedule_name: str,
        schedule_type: str,
        schedule_date: datetime,
        status: str,
        created_by_user_id: int,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Initialize Schedule entity.

        Args:
            id: Schedule ID (None for new schedules)
            organization_id: Organization ID
            plant_id: Plant ID
            schedule_number: Unique schedule number
            schedule_name: Human-readable schedule name
            schedule_type: DAILY, WEEKLY, or MONTHLY
            schedule_date: Date of the schedule
            status: DRAFT, PUBLISHED, or ACTIVE
            created_by_user_id: User who created the schedule
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.organization_id = organization_id
        self.plant_id = plant_id
        self.schedule_number = schedule_number
        self.schedule_name = schedule_name
        self.schedule_type = schedule_type
        self.schedule_date = schedule_date
        self.status = status
        self.created_by_user_id = created_by_user_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.scheduled_operations: List = []

    def publish(self) -> None:
        """
        Transition schedule from DRAFT to PUBLISHED.

        Raises:
            ValueError: If schedule is not in DRAFT status
        """
        if self.status != 'DRAFT':
            raise ValueError(f"Cannot publish schedule with status {self.status}")

        self.status = 'PUBLISHED'
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """
        Transition schedule from PUBLISHED to ACTIVE.

        Raises:
            ValueError: If schedule is not in PUBLISHED status
        """
        if self.status != 'PUBLISHED':
            raise ValueError(f"Cannot activate schedule with status {self.status}")

        self.status = 'ACTIVE'
        self.updated_at = datetime.utcnow()

    def get_gantt_chart_data(self) -> Dict[int, List]:
        """
        Get operations grouped by work center for Gantt chart visualization.

        Returns:
            Dictionary mapping work_center_id to list of scheduled operations
        """
        gantt_data: Dict[int, List] = {}

        for operation in self.scheduled_operations:
            work_center_id = operation.work_center_id

            if work_center_id not in gantt_data:
                gantt_data[work_center_id] = []

            gantt_data[work_center_id].append(operation)

        return gantt_data
