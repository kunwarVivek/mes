"""
Domain service for capacity calculation and scheduling.
Phase 3: Production Planning Module - Component 3
Enhanced with multi-shift support.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models.work_order import WorkCenter, WorkOrderOperation
from app.models.work_center_shift import WorkCenterShift


logger = logging.getLogger(__name__)


class CapacityCalculator:
    """
    Domain service for work center capacity calculations.

    Provides methods to:
    - Calculate work center load for a time period
    - Find available time slots for scheduling
    - Identify capacity bottlenecks
    """

    def __init__(self, db_session: Session, use_shift_calendar: bool = False):
        """
        Initialize capacity calculator.

        Args:
            db_session: SQLAlchemy database session
            use_shift_calendar: If True, use shift calendar for capacity calculations.
                                If False, use legacy 8-hour/day calculation (default for backward compatibility).
        """
        self.db_session = db_session
        self.use_shift_calendar = use_shift_calendar

    def calculate_work_center_load(
        self,
        work_center_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """
        Calculate total hours loaded on work center for time period.

        Args:
            work_center_id: ID of the work center
            start_date: Period start date
            end_date: Period end date

        Returns:
            Dictionary with:
            - total_hours: Total hours loaded
            - capacity_hours: Total capacity available
            - utilization_pct: Utilization percentage
            - available_hours: Remaining available hours
        """
        # Get work center
        work_center = self.db_session.query(WorkCenter).filter(
            WorkCenter.id == work_center_id
        ).first()

        if not work_center:
            raise ValueError(f"Work center {work_center_id} not found")

        # Calculate total capacity hours
        if self.use_shift_calendar:
            # Use shift calendar for accurate capacity calculation
            capacity_hours = self._calculate_shift_based_capacity(
                work_center_id, start_date, end_date
            )
        else:
            # Legacy calculation: Assume 8 hours per day, 7 days per week
            days = (end_date - start_date).days + 1  # +1 to include end_date
            capacity_hours = days * 8.0

        # Get all operations scheduled for this work center in the period
        operations = self.db_session.query(WorkOrderOperation).filter(
            WorkOrderOperation.work_center_id == work_center_id,
            WorkOrderOperation.start_time >= start_date,
            WorkOrderOperation.end_time <= end_date
        ).all()

        # Calculate total loaded hours
        total_hours = 0.0
        for operation in operations:
            # Get work order to determine quantity
            work_order = operation.work_order
            if work_order:
                # Calculate hours: setup + (run_time_per_unit * quantity)
                setup_hours = operation.setup_time_minutes / 60.0
                run_hours = (operation.run_time_per_unit_minutes * work_order.planned_quantity) / 60.0
                total_hours += setup_hours + run_hours

        # Calculate utilization
        utilization_pct = (total_hours / capacity_hours * 100.0) if capacity_hours > 0 else 0.0
        available_hours = max(0.0, capacity_hours - total_hours)

        logger.info(
            f"Work center {work_center_id} load: {total_hours:.1f}/{capacity_hours:.1f} hours "
            f"({utilization_pct:.1f}% utilization)"
        )

        return {
            'total_hours': total_hours,
            'capacity_hours': capacity_hours,
            'utilization_pct': utilization_pct,
            'available_hours': available_hours
        }

    def find_available_time_slot(
        self,
        work_center_id: int,
        hours_needed: float,
        earliest_start: datetime,
        max_search_days: int = 365
    ) -> datetime:
        """
        Find next available time slot on work center.

        Args:
            work_center_id: ID of the work center
            hours_needed: Number of hours needed
            earliest_start: Earliest possible start time
            max_search_days: Maximum days to search ahead

        Returns:
            Start datetime for scheduling the operation

        Raises:
            ValueError: If no available time slot found within search window
        """
        # Get work center
        work_center = self.db_session.query(WorkCenter).filter(
            WorkCenter.id == work_center_id
        ).first()

        if not work_center:
            raise ValueError(f"Work center {work_center_id} not found")

        # Get all operations for this work center, sorted by end time
        operations = self.db_session.query(WorkOrderOperation).filter(
            WorkOrderOperation.work_center_id == work_center_id,
            WorkOrderOperation.end_time.isnot(None)
        ).order_by(WorkOrderOperation.end_time).all()

        # If no operations, earliest_start is available
        if not operations:
            logger.info(
                f"Found available slot for work center {work_center_id} at {earliest_start}, "
                f"no existing operations"
            )
            return earliest_start

        # Find first gap that fits the requirement
        # Check if we can start before first operation
        first_op_start = min(op.start_time for op in operations if op.start_time)
        if first_op_start and earliest_start < first_op_start:
            # Check if there's enough time before first operation
            hours_before_first = (first_op_start - earliest_start).total_seconds() / 3600
            if hours_before_first >= hours_needed:
                logger.info(
                    f"Found available slot for work center {work_center_id} at {earliest_start}, "
                    f"before first operation"
                )
                return earliest_start

        # Check gaps between operations
        for i in range(len(operations) - 1):
            current_op = operations[i]
            next_op = operations[i + 1]

            if current_op.end_time and next_op.start_time:
                gap_hours = (next_op.start_time - current_op.end_time).total_seconds() / 3600
                gap_start = max(current_op.end_time, earliest_start)

                if gap_hours >= hours_needed and gap_start >= earliest_start:
                    logger.info(
                        f"Found available slot for work center {work_center_id} at {gap_start}, "
                        f"gap between operations"
                    )
                    return gap_start

        # Check after last operation
        last_op_end = max(op.end_time for op in operations if op.end_time)
        if last_op_end:
            slot_start = max(last_op_end, earliest_start)
            max_end = earliest_start + timedelta(days=max_search_days)

            if slot_start < max_end:
                logger.info(
                    f"Found available slot for work center {work_center_id} at {slot_start}, "
                    f"after last operation"
                )
                return slot_start

        # No slot found
        raise ValueError(
            f"No available time slot found for work center {work_center_id} "
            f"requiring {hours_needed} hours within {max_search_days} days"
        )

    def calculate_operation_hours(
        self,
        setup_time_minutes: float,
        run_time_per_unit_minutes: float,
        quantity: float
    ) -> float:
        """
        Calculate total hours needed for an operation.

        Args:
            setup_time_minutes: Setup time in minutes
            run_time_per_unit_minutes: Run time per unit in minutes
            quantity: Number of units

        Returns:
            Total hours needed
        """
        setup_hours = setup_time_minutes / 60.0
        run_hours = (run_time_per_unit_minutes * quantity) / 60.0
        return setup_hours + run_hours

    def _calculate_shift_based_capacity(
        self,
        work_center_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """
        Calculate capacity based on work center shift calendar.

        This method iterates through each day in the period and sums
        the capacity from all active shifts, accounting for:
        - Different shifts on different days (weekday vs weekend)
        - Capacity percentage (efficiency factors)
        - Inactive shifts

        Args:
            work_center_id: Work center ID
            start_date: Period start date
            end_date: Period end date

        Returns:
            Total capacity hours for the period
        """
        from app.domain.services.shift_calendar_service import ShiftCalendarService

        shift_service = ShiftCalendarService(self.db_session)
        total_capacity = shift_service.calculate_period_capacity(
            work_center_id, start_date, end_date
        )

        logger.debug(
            f"Shift-based capacity for work center {work_center_id} "
            f"from {start_date.date()} to {end_date.date()}: {total_capacity:.1f} hours"
        )

        return total_capacity
