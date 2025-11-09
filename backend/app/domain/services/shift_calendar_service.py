"""
Domain service for shift calendar operations and capacity calculations.
Work Center Multi-Shift Support - Production Planning Module

Provides shift-aware capacity calculations and scheduling logic.
"""
import logging
from datetime import datetime, time, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.work_center_shift import WorkCenterShift


logger = logging.getLogger(__name__)


class ShiftCalendarService:
    """
    Domain service for work center shift calendar operations.

    Provides methods to:
    - Detect shift overlaps
    - Calculate capacity across multiple shifts
    - Handle shift transitions and downtime
    - Support shift-aware scheduling
    """

    def __init__(self, db_session: Session):
        """
        Initialize shift calendar service.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    def detect_shift_overlap(
        self,
        work_center_id: int,
        new_start_time: time,
        new_end_time: time,
        new_days_of_week: List[int],
        exclude_shift_id: Optional[int] = None
    ) -> bool:
        """
        Detect if a new shift overlaps with existing active shifts.

        Args:
            work_center_id: Work center ID
            new_start_time: Proposed shift start time
            new_end_time: Proposed shift end time
            new_days_of_week: Days when shift operates
            exclude_shift_id: Optional shift ID to exclude (for updates)

        Returns:
            True if overlap detected, False otherwise
        """
        # Get all active shifts for this work center
        query = self.db_session.query(WorkCenterShift).filter(
            WorkCenterShift.work_center_id == work_center_id,
            WorkCenterShift.is_active == True
        )

        if exclude_shift_id:
            query = query.filter(WorkCenterShift.id != exclude_shift_id)

        existing_shifts = query.all()

        # Check each existing shift for overlap
        for existing_shift in existing_shifts:
            # Check if days overlap
            common_days = set(new_days_of_week) & set(existing_shift.days_of_week)
            if not common_days:
                continue  # No day overlap, skip time check

            # Check if times overlap on common days
            if self._times_overlap(
                new_start_time, new_end_time,
                existing_shift.start_time, existing_shift.end_time
            ):
                logger.warning(
                    f"Shift overlap detected: new shift ({new_start_time}-{new_end_time}) "
                    f"overlaps with existing shift '{existing_shift.shift_name}' "
                    f"({existing_shift.start_time}-{existing_shift.end_time}) "
                    f"on days {common_days}"
                )
                return True

        return False

    def _times_overlap(
        self,
        start1: time,
        end1: time,
        start2: time,
        end2: time
    ) -> bool:
        """
        Check if two time ranges overlap.

        Handles shifts that span midnight (e.g., 22:00-06:00).

        Args:
            start1, end1: First time range
            start2, end2: Second time range

        Returns:
            True if ranges overlap
        """
        # Convert to minutes since midnight for easier comparison
        def time_to_minutes(t: time) -> int:
            return t.hour * 60 + t.minute

        # Convert times to minutes
        s1 = time_to_minutes(start1)
        e1 = time_to_minutes(end1)
        s2 = time_to_minutes(start2)
        e2 = time_to_minutes(end2)

        # Handle midnight spanning for first shift
        if e1 <= s1:  # Spans midnight
            e1 += 24 * 60

        # Handle midnight spanning for second shift
        if e2 <= s2:  # Spans midnight
            e2 += 24 * 60

        # For midnight-spanning shifts, also check the wrapped-around version
        # Shift 1 might span midnight, so check both [s1, e1] and [s1+1440, e1+1440]
        # Shift 2 might span midnight, so check both [s2, e2] and [s2+1440, e2+1440]

        # Standard overlap check
        if max(s1, s2) < min(e1, e2):
            return True

        # Check if shift2 wraps around and overlaps with shift1
        if s2 > e2:  # shift2 spans midnight
            # Check overlap with the part after midnight
            if max(s1, s2) < min(e1, e2 + 24 * 60):
                return True
            # Check overlap with the part before midnight
            if max(s1, s2 - 24 * 60) < min(e1, e2):
                return True

        # Check if shift1 wraps around and overlaps with shift2
        if s1 > e1:  # shift1 spans midnight (already handled by e1 += 24*60 above)
            # Additional check for edge cases
            if max(s1 - 24 * 60, s2) < min(e1 - 24 * 60, e2):
                return True

        return False

    def calculate_daily_capacity(
        self,
        work_center_id: int,
        target_date: datetime
    ) -> float:
        """
        Calculate total capacity hours for a specific date.

        Sums capacity from all active shifts operating on that day,
        accounting for capacity_percentage.

        Args:
            work_center_id: Work center ID
            target_date: Date to calculate capacity for

        Returns:
            Total capacity hours (effective hours considering efficiency)
        """
        # Get day of week (ISO format: 1=Monday, 7=Sunday)
        day_of_week = target_date.isoweekday()

        # Get active shifts for this work center and day
        active_shifts = self.get_active_shifts_for_date(work_center_id, target_date)

        total_capacity = 0.0
        for shift in active_shifts:
            # Calculate shift duration
            shift_hours = shift.get_shift_duration_hours()

            # Apply capacity percentage (efficiency factor)
            effective_hours = shift_hours * (shift.capacity_percentage / 100.0)

            total_capacity += effective_hours

            logger.debug(
                f"Shift '{shift.shift_name}' on {target_date.date()}: "
                f"{shift_hours:.1f}h * {shift.capacity_percentage}% = {effective_hours:.1f}h"
            )

        logger.info(
            f"Total capacity for work center {work_center_id} on {target_date.date()}: "
            f"{total_capacity:.1f} hours"
        )

        return total_capacity

    def get_active_shifts_for_date(
        self,
        work_center_id: int,
        target_date: datetime
    ) -> List[WorkCenterShift]:
        """
        Get all active shifts for a work center on a specific date.

        Args:
            work_center_id: Work center ID
            target_date: Target date

        Returns:
            List of active shifts operating on that date
        """
        # Get day of week (ISO format: 1=Monday, 7=Sunday)
        day_of_week = target_date.isoweekday()

        # Query active shifts for this work center
        shifts = self.db_session.query(WorkCenterShift).filter(
            WorkCenterShift.work_center_id == work_center_id,
            WorkCenterShift.is_active == True
        ).all()

        # Filter shifts that operate on this day of week
        active_shifts = [
            shift for shift in shifts
            if shift.is_active_on_day(day_of_week)
        ]

        return active_shifts

    def calculate_period_capacity(
        self,
        work_center_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """
        Calculate total capacity for a date range.

        Args:
            work_center_id: Work center ID
            start_date: Period start date
            end_date: Period end date (inclusive)

        Returns:
            Total capacity hours across the period
        """
        total_capacity = 0.0
        current_date = start_date

        # Iterate through each day in the range
        while current_date <= end_date:
            daily_capacity = self.calculate_daily_capacity(work_center_id, current_date)
            total_capacity += daily_capacity
            current_date += timedelta(days=1)

        logger.info(
            f"Total capacity for work center {work_center_id} "
            f"from {start_date.date()} to {end_date.date()}: "
            f"{total_capacity:.1f} hours"
        )

        return total_capacity

    def get_shift_transitions(
        self,
        work_center_id: int,
        target_date: datetime
    ) -> List[dict]:
        """
        Get shift transition times for a specific date.

        Useful for identifying downtime periods and shift changeovers.

        Args:
            work_center_id: Work center ID
            target_date: Target date

        Returns:
            List of transition events with times and shift info
        """
        active_shifts = self.get_active_shifts_for_date(work_center_id, target_date)

        if not active_shifts:
            return []

        transitions = []
        for shift in active_shifts:
            transitions.append({
                'event': 'shift_start',
                'time': shift.start_time,
                'shift_name': shift.shift_name,
                'shift_number': shift.shift_number
            })
            transitions.append({
                'event': 'shift_end',
                'time': shift.end_time,
                'shift_name': shift.shift_name,
                'shift_number': shift.shift_number
            })

        # Sort by time
        transitions.sort(key=lambda x: (x['time'].hour, x['time'].minute))

        return transitions
