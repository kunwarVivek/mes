"""
ScheduledOperation domain entity - scheduled time slot for operation.
Phase 3: Production Planning Module - Component 6
"""
from datetime import datetime
from typing import List, Optional


class ScheduledOperation:
    """
    ScheduledOperation domain entity representing a scheduled time slot.

    Represents when and where a work order operation is scheduled to run.
    Includes predecessor relationships and critical path information.
    """

    def __init__(
        self,
        id: Optional[int],
        schedule_id: int,
        work_order_operation_id: int,
        work_center_id: int,
        scheduled_start: datetime,
        scheduled_end: datetime,
        predecessor_operation_ids: List[int],
        slack_time_minutes: int,
        is_critical_path: bool,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Initialize ScheduledOperation entity.

        Args:
            id: Scheduled operation ID (None for new)
            schedule_id: Parent schedule ID
            work_order_operation_id: Work order operation being scheduled
            work_center_id: Work center where operation is scheduled
            scheduled_start: Scheduled start datetime
            scheduled_end: Scheduled end datetime
            predecessor_operation_ids: List of predecessor operation IDs
            slack_time_minutes: Slack time (float) in minutes
            is_critical_path: Whether operation is on critical path
            created_at: Creation timestamp
            updated_at: Last update timestamp

        Raises:
            ValueError: If scheduled_end is not after scheduled_start
        """
        if scheduled_end <= scheduled_start:
            raise ValueError("scheduled_end must be after scheduled_start")

        self.id = id
        self.schedule_id = schedule_id
        self.work_order_operation_id = work_order_operation_id
        self.work_center_id = work_center_id
        self.scheduled_start = scheduled_start
        self.scheduled_end = scheduled_end
        self.predecessor_operation_ids = predecessor_operation_ids
        self.slack_time_minutes = slack_time_minutes
        self.is_critical_path = is_critical_path
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at

    def calculate_duration(self) -> int:
        """
        Calculate duration in minutes.

        Returns:
            Duration in minutes
        """
        duration_seconds = (self.scheduled_end - self.scheduled_start).total_seconds()
        return int(duration_seconds / 60)

    def check_predecessor_complete(self, completed_operation_ids: List[int]) -> bool:
        """
        Check if all predecessor operations are complete.

        Args:
            completed_operation_ids: List of completed operation IDs

        Returns:
            True if all predecessors are complete, False otherwise
        """
        for predecessor_id in self.predecessor_operation_ids:
            if predecessor_id not in completed_operation_ids:
                return False
        return True
