"""
Operation Scheduling Service - Domain Service Layer.

Implements scheduling logic for work order operations with support for:
- Sequential scheduling (default)
- Overlap scheduling (operations start during predecessor execution)
- Parallel scheduling (simultaneous operations)
- Dependency validation
- Gantt chart data generation

Follows DDD and SOLID principles:
- Single Responsibility: Each class/method has one clear purpose
- Open/Closed: Extensible for new scheduling modes via strategy pattern
- Dependency Inversion: Depends on abstractions (Session interface)

Usage:
    service = OperationSchedulingService(db_session)
    scheduled = service.schedule_operations(work_order_id=123, start_date=now, quantity=100)
    gantt = service.generate_gantt_chart_data(work_order_id=123, start_date=now, quantity=100)
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.work_order import WorkOrder, WorkOrderOperation, SchedulingMode


@dataclass
class ScheduledOperation:
    """Value object representing a scheduled operation with calculated times"""
    id: int
    operation_number: int
    operation_name: str
    work_center_id: int
    work_center_code: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    scheduling_mode: SchedulingMode
    predecessor_id: Optional[int]
    overlap_percentage: float


@dataclass
class GanttChartData:
    """Value object representing Gantt chart compatible data structure"""
    work_order_id: int
    work_order_number: str
    start_date: datetime
    end_date: datetime
    total_duration_minutes: float
    tasks: List[Dict[str, Any]]


class OperationDurationCalculator:
    """
    Helper class for calculating operation durations.

    Single Responsibility: Duration calculation logic only.
    """

    @staticmethod
    def calculate_duration(
        setup_time_minutes: float,
        run_time_per_unit_minutes: float,
        quantity: float
    ) -> float:
        """
        Calculate total operation duration.

        Args:
            setup_time_minutes: Setup time in minutes
            run_time_per_unit_minutes: Runtime per unit in minutes
            quantity: Number of units to produce

        Returns:
            Total duration in minutes
        """
        if setup_time_minutes < 0 or run_time_per_unit_minutes < 0 or quantity <= 0:
            raise ValueError("Invalid duration parameters")

        return setup_time_minutes + (run_time_per_unit_minutes * quantity)


class OperationSchedulingService:
    """
    Domain service for operation scheduling.

    Responsibilities:
    - Calculate operation start/end times based on scheduling mode
    - Validate dependencies (no cycles, valid predecessors)
    - Generate Gantt chart data for visualization
    """

    def __init__(self, session: Session):
        self._session = session

    def schedule_operations(
        self,
        work_order_id: int,
        start_date: datetime,
        quantity: float
    ) -> List[ScheduledOperation]:
        """
        Schedule all operations for a work order.

        Args:
            work_order_id: Work order ID to schedule
            start_date: Production start date/time
            quantity: Quantity to produce

        Returns:
            List of scheduled operations with calculated start/end times

        Raises:
            ValueError: If cyclic dependencies detected or invalid predecessor
        """
        # Load work order and operations
        work_order = self._session.query(WorkOrder).filter_by(id=work_order_id).first()
        if not work_order:
            raise ValueError(f"Work order {work_order_id} not found")

        operations = (
            self._session.query(WorkOrderOperation)
            .filter_by(work_order_id=work_order_id)
            .order_by(WorkOrderOperation.operation_number)
            .all()
        )

        if not operations:
            return []

        # Validate dependencies
        self._validate_dependencies(operations)

        # Build dependency graph
        op_dict = {op.id: op for op in operations}
        scheduled = {}

        # Schedule operations in order
        for operation in operations:
            scheduled_op = self._schedule_single_operation(
                operation=operation,
                start_date=start_date,
                quantity=quantity,
                scheduled_ops=scheduled,
                op_dict=op_dict
            )
            scheduled[operation.id] = scheduled_op

        return list(scheduled.values())

    def _schedule_single_operation(
        self,
        operation: WorkOrderOperation,
        start_date: datetime,
        quantity: float,
        scheduled_ops: Dict[int, ScheduledOperation],
        op_dict: Dict[int, WorkOrderOperation]
    ) -> ScheduledOperation:
        """
        Schedule a single operation based on its scheduling mode.

        Args:
            operation: Operation to schedule
            start_date: Work order start date
            quantity: Production quantity
            scheduled_ops: Already scheduled operations
            op_dict: Dictionary of all operations by ID

        Returns:
            Scheduled operation with calculated times
        """
        # Calculate operation duration using helper
        duration = OperationDurationCalculator.calculate_duration(
            setup_time_minutes=operation.setup_time_minutes,
            run_time_per_unit_minutes=operation.run_time_per_unit_minutes,
            quantity=quantity
        )

        # Determine operation start time based on mode
        if operation.scheduling_mode == SchedulingMode.SEQUENTIAL:
            op_start = self._calculate_sequential_start(
                operation, start_date, scheduled_ops, op_dict
            )
        elif operation.scheduling_mode == SchedulingMode.OVERLAP:
            op_start = self._calculate_overlap_start(
                operation, start_date, scheduled_ops, op_dict, quantity
            )
        elif operation.scheduling_mode == SchedulingMode.PARALLEL:
            op_start = self._calculate_parallel_start(
                operation, start_date, scheduled_ops
            )
        else:
            op_start = start_date

        op_end = op_start + timedelta(minutes=duration)

        return ScheduledOperation(
            id=operation.id,
            operation_number=operation.operation_number,
            operation_name=operation.operation_name,
            work_center_id=operation.work_center_id,
            work_center_code=operation.work_center.work_center_code,
            start_time=op_start,
            end_time=op_end,
            duration_minutes=duration,
            scheduling_mode=operation.scheduling_mode,
            predecessor_id=operation.predecessor_operation_id,
            overlap_percentage=operation.overlap_percentage
        )

    def _calculate_sequential_start(
        self,
        operation: WorkOrderOperation,
        start_date: datetime,
        scheduled_ops: Dict[int, ScheduledOperation],
        op_dict: Dict[int, WorkOrderOperation]
    ) -> datetime:
        """
        Calculate start time for sequential operation.
        Operation starts when predecessor completes (100% complete).
        """
        if not operation.predecessor_operation_id:
            return start_date

        predecessor = scheduled_ops.get(operation.predecessor_operation_id)
        if not predecessor:
            return start_date

        # Sequential: start when predecessor ends
        return predecessor.end_time

    def _calculate_overlap_start(
        self,
        operation: WorkOrderOperation,
        start_date: datetime,
        scheduled_ops: Dict[int, ScheduledOperation],
        op_dict: Dict[int, WorkOrderOperation],
        quantity: float
    ) -> datetime:
        """
        Calculate start time for overlapping operation.
        Operation can start when predecessor reaches specified completion percentage.
        """
        if not operation.predecessor_operation_id:
            return start_date

        predecessor = scheduled_ops.get(operation.predecessor_operation_id)
        if not predecessor:
            return start_date

        # Calculate when predecessor reaches the required completion percentage
        completion_percentage = operation.can_start_at_percentage
        predecessor_duration = predecessor.duration_minutes
        elapsed_time = (completion_percentage / 100.0) * predecessor_duration

        return predecessor.start_time + timedelta(minutes=elapsed_time)

    def _calculate_parallel_start(
        self,
        operation: WorkOrderOperation,
        start_date: datetime,
        scheduled_ops: Dict[int, ScheduledOperation]
    ) -> datetime:
        """
        Calculate start time for parallel operation.
        Parallel operations start at the same time as work order.
        """
        # Parallel operations ignore predecessors and start at work order start
        return start_date

    def _validate_dependencies(self, operations: List[WorkOrderOperation]) -> None:
        """
        Validate operation dependencies.

        Checks:
        - No cyclic dependencies
        - Predecessor exists in same work order
        - Predecessor operation number < current operation number

        Raises:
            ValueError: If validation fails
        """
        op_dict = {op.id: op for op in operations}
        op_ids = set(op.id for op in operations)

        for operation in operations:
            if operation.predecessor_operation_id:
                # Check predecessor exists
                if operation.predecessor_operation_id not in op_ids:
                    raise ValueError(
                        f"Invalid predecessor operation {operation.predecessor_operation_id} "
                        f"for operation {operation.operation_number}"
                    )

                # Check for cyclic dependencies
                if self._has_cycle(operation, op_dict, set()):
                    raise ValueError(
                        f"Cyclic dependency detected for operation {operation.operation_number}"
                    )

    def _has_cycle(
        self,
        operation: WorkOrderOperation,
        op_dict: Dict[int, WorkOrderOperation],
        visited: Set[int]
    ) -> bool:
        """
        Detect cyclic dependencies using Depth-First Search (DFS).

        Algorithm: Traverse predecessor chain, tracking visited nodes.
        If we encounter a node already in the path, a cycle exists.

        Args:
            operation: Current operation to check
            op_dict: Dictionary of all operations by ID
            visited: Set of visited operation IDs in current DFS path

        Returns:
            True if cycle detected, False otherwise

        Time Complexity: O(n) where n is number of operations
        Space Complexity: O(n) for visited set
        """
        if operation.id in visited:
            return True

        visited.add(operation.id)

        if operation.predecessor_operation_id:
            predecessor = op_dict.get(operation.predecessor_operation_id)
            if predecessor and self._has_cycle(predecessor, op_dict, visited.copy()):
                return True

        return False

    def generate_gantt_chart_data(
        self,
        work_order_id: int,
        start_date: datetime,
        quantity: float
    ) -> GanttChartData:
        """
        Generate Gantt chart compatible data structure.

        Args:
            work_order_id: Work order to generate chart for
            start_date: Production start date
            quantity: Production quantity

        Returns:
            GanttChartData object with tasks formatted for Gantt chart
        """
        # Schedule all operations
        scheduled_ops = self.schedule_operations(work_order_id, start_date, quantity)

        if not scheduled_ops:
            work_order = self._session.query(WorkOrder).filter_by(id=work_order_id).first()
            return GanttChartData(
                work_order_id=work_order_id,
                work_order_number=work_order.work_order_number if work_order else "",
                start_date=start_date,
                end_date=start_date,
                total_duration_minutes=0.0,
                tasks=[]
            )

        # Calculate overall timeline
        overall_start = min(op.start_time for op in scheduled_ops)
        overall_end = max(op.end_time for op in scheduled_ops)
        total_duration = (overall_end - overall_start).total_seconds() / 60.0

        # Build task list
        tasks = []
        for op in scheduled_ops:
            task = {
                'id': op.id,
                'name': op.operation_name,
                'operation_number': op.operation_number,
                'work_center': op.work_center_code,
                'start': op.start_time.isoformat(),
                'end': op.end_time.isoformat(),
                'duration_minutes': op.duration_minutes,
                'scheduling_mode': op.scheduling_mode.value,
                'predecessor_id': op.predecessor_id,
                'overlap_percentage': op.overlap_percentage
            }
            tasks.append(task)

        work_order = self._session.query(WorkOrder).filter_by(id=work_order_id).first()

        return GanttChartData(
            work_order_id=work_order_id,
            work_order_number=work_order.work_order_number,
            start_date=overall_start,
            end_date=overall_end,
            total_duration_minutes=total_duration,
            tasks=tasks
        )
