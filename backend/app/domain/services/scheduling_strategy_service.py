"""
Scheduling Strategy domain service - implements scheduling algorithms.
Phase 3: Production Planning Module - Component 6
"""
import logging
from datetime import datetime
from typing import List


logger = logging.getLogger(__name__)


class SchedulingStrategyService:
    """
    Domain service for production scheduling strategies.

    Provides different scheduling algorithms:
    - Earliest Due Date (EDD)
    - Shortest Processing Time (SPT)
    - Critical Ratio (CR)
    """

    def earliest_due_date(self, work_orders: List) -> List:
        """
        Sort work orders by due date (earliest first).

        Args:
            work_orders: List of WorkOrder entities

        Returns:
            Sorted list of work orders (earliest due date first)
        """
        sorted_orders = sorted(
            work_orders,
            key=lambda wo: wo.end_date_planned if wo.end_date_planned else datetime.max
        )

        logger.info(f"Sorted {len(work_orders)} work orders by earliest due date")
        return sorted_orders

    def shortest_processing_time(self, work_orders: List) -> List:
        """
        Sort work orders by total processing time (shortest first).

        Args:
            work_orders: List of WorkOrder entities with operations

        Returns:
            Sorted list of work orders (shortest processing time first)
        """
        def calculate_processing_time(work_order):
            """Calculate total processing time for work order"""
            total_time = 0.0
            for operation in work_order.operations:
                setup_time = operation.setup_time_minutes
                run_time = operation.run_time_per_unit_minutes * work_order.planned_quantity
                total_time += setup_time + run_time
            return total_time

        sorted_orders = sorted(work_orders, key=calculate_processing_time)

        logger.info(f"Sorted {len(work_orders)} work orders by shortest processing time")
        return sorted_orders

    def critical_ratio(self, work_orders: List, current_date: datetime) -> List:
        """
        Sort work orders by critical ratio (most urgent first).

        Critical Ratio = (due_date - current_date) / total_processing_time
        Lower CR = more urgent (CR < 1 means late)

        Args:
            work_orders: List of WorkOrder entities with operations
            current_date: Current date for calculation

        Returns:
            Sorted list of work orders (lowest CR / most urgent first)
        """
        def calculate_critical_ratio(work_order):
            """Calculate critical ratio for work order"""
            # Calculate processing time in hours
            total_time_minutes = 0.0
            for operation in work_order.operations:
                setup_time = operation.setup_time_minutes
                run_time = operation.run_time_per_unit_minutes * work_order.planned_quantity
                total_time_minutes += setup_time + run_time

            total_time_hours = total_time_minutes / 60.0

            if total_time_hours == 0:
                return float('inf')  # No processing time, low priority

            # Calculate time until due date in days
            if work_order.end_date_planned:
                time_until_due = (work_order.end_date_planned - current_date).total_seconds() / 3600  # hours
                critical_ratio = time_until_due / total_time_hours
                return critical_ratio
            else:
                return float('inf')  # No due date, low priority

        sorted_orders = sorted(work_orders, key=calculate_critical_ratio)

        logger.info(f"Sorted {len(work_orders)} work orders by critical ratio")
        return sorted_orders
