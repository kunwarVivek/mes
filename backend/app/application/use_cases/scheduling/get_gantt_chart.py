"""
Get Gantt Chart Use Case

Generates Gantt chart data for work orders with operations, lanes, and dependencies.
"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.infrastructure.repositories.scheduling_repository import SchedulingRepository
from app.domain.services.operation_scheduling_service import (
    OperationSchedulingService,
    GanttChartData
)
from app.models.work_order import WorkOrder
from app.core.exceptions import ValidationException


class GetGanttChartDTO:
    """Data Transfer Object for Gantt chart request."""

    def __init__(
        self,
        plant_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        lane_ids: Optional[List[int]] = None,
        include_completed: bool = False,
        organization_id: Optional[int] = None
    ):
        self.plant_id = plant_id
        self.start_date = start_date
        self.end_date = end_date
        self.lane_ids = lane_ids
        self.include_completed = include_completed
        self.organization_id = organization_id


class GanttChartTask:
    """Value object for a single Gantt chart task."""

    def __init__(
        self,
        work_order_id: int,
        work_order_number: str,
        operation_id: Optional[int],
        operation_name: Optional[str],
        operation_number: Optional[int],
        start_date: datetime,
        end_date: datetime,
        duration_hours: float,
        lane_id: Optional[int],
        lane_code: Optional[str],
        dependencies: List[int],
        progress_percent: float,
        status: str,
        is_critical_path: bool = False,
        scheduling_mode: Optional[str] = None
    ):
        self.work_order_id = work_order_id
        self.work_order_number = work_order_number
        self.operation_id = operation_id
        self.operation_name = operation_name
        self.operation_number = operation_number
        self.start_date = start_date
        self.end_date = end_date
        self.duration_hours = duration_hours
        self.lane_id = lane_id
        self.lane_code = lane_code
        self.dependencies = dependencies
        self.progress_percent = progress_percent
        self.status = status
        self.is_critical_path = is_critical_path
        self.scheduling_mode = scheduling_mode


class GanttChartResponse:
    """Value object for complete Gantt chart response."""

    def __init__(
        self,
        tasks: List[GanttChartTask],
        conflicts: List[dict],
        critical_path: List[int],
        start_date: datetime,
        end_date: datetime,
        total_work_orders: int
    ):
        self.tasks = tasks
        self.conflicts = conflicts
        self.critical_path = critical_path
        self.start_date = start_date
        self.end_date = end_date
        self.total_work_orders = total_work_orders


class GetGanttChartUseCase:
    """
    Use case for generating Gantt chart visualization data.

    Business Logic:
    1. Query work orders for the given filters (plant, date range, lanes)
    2. For each work order, generate operation schedule using domain service
    3. Aggregate all tasks into single Gantt chart
    4. Detect lane conflicts (multiple WOs on same lane at same time)
    5. Calculate critical path (longest sequence of dependent operations)
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = SchedulingRepository(db)
        self.scheduling_service = OperationSchedulingService(db)

    def execute(self, dto: GetGanttChartDTO) -> GanttChartResponse:
        """
        Execute Gantt chart generation.

        Args:
            dto: GetGanttChartDTO with filters

        Returns:
            GanttChartResponse with tasks, conflicts, critical path

        Raises:
            ValidationException: If date range is invalid
        """
        # Validate date range
        if dto.start_date and dto.end_date and dto.start_date > dto.end_date:
            raise ValidationException(
                "Start date must be before or equal to end date",
                field="start_date"
            )

        # Get work orders matching filters
        work_orders = self.repo.get_work_orders_for_gantt(
            plant_id=dto.plant_id,
            start_date=dto.start_date,
            end_date=dto.end_date,
            lane_ids=dto.lane_ids,
            include_completed=dto.include_completed,
            organization_id=dto.organization_id
        )

        if not work_orders:
            # Return empty chart
            return GanttChartResponse(
                tasks=[],
                conflicts=[],
                critical_path=[],
                start_date=datetime.now(),
                end_date=datetime.now(),
                total_work_orders=0
            )

        # Generate tasks for all work orders
        tasks = []
        all_start_dates = []
        all_end_dates = []

        for work_order in work_orders:
            # Get lane assignment
            lane_assignment = work_order.lane_assignments[0] if work_order.lane_assignments else None

            if work_order.operations:
                # Generate operation-level tasks using domain service
                try:
                    gantt_data = self.scheduling_service.generate_gantt_chart_data(
                        work_order_id=work_order.id,
                        start_date=work_order.planned_start_date,
                        quantity=work_order.quantity_ordered
                    )

                    # Convert to tasks
                    for task_data in gantt_data.tasks:
                        task = GanttChartTask(
                            work_order_id=work_order.id,
                            work_order_number=work_order.work_order_number,
                            operation_id=task_data['id'],
                            operation_name=task_data['name'],
                            operation_number=task_data['operation_number'],
                            start_date=datetime.fromisoformat(task_data['start']),
                            end_date=datetime.fromisoformat(task_data['end']),
                            duration_hours=task_data['duration_minutes'] / 60.0,
                            lane_id=lane_assignment.lane_id if lane_assignment else None,
                            lane_code=lane_assignment.lane.lane_code if lane_assignment and lane_assignment.lane else None,
                            dependencies=[task_data['predecessor_id']] if task_data.get('predecessor_id') else [],
                            progress_percent=self._calculate_operation_progress(work_order, task_data['id']),
                            status=work_order.order_status.value,
                            scheduling_mode=task_data.get('scheduling_mode')
                        )
                        tasks.append(task)

                        all_start_dates.append(task.start_date)
                        all_end_dates.append(task.end_date)

                except Exception as e:
                    # Log error but continue with other work orders
                    print(f"Error generating Gantt for WO {work_order.work_order_number}: {e}")
                    continue
            else:
                # Work order level task (no operations defined)
                task = GanttChartTask(
                    work_order_id=work_order.id,
                    work_order_number=work_order.work_order_number,
                    operation_id=None,
                    operation_name=work_order.product.description if work_order.product else "Production",
                    operation_number=None,
                    start_date=work_order.planned_start_date,
                    end_date=work_order.planned_end_date,
                    duration_hours=(work_order.planned_end_date - work_order.planned_start_date).total_seconds() / 3600.0,
                    lane_id=lane_assignment.lane_id if lane_assignment else None,
                    lane_code=lane_assignment.lane.lane_code if lane_assignment and lane_assignment.lane else None,
                    dependencies=[work_order.predecessor_work_order_id] if work_order.predecessor_work_order_id else [],
                    progress_percent=self._calculate_work_order_progress(work_order),
                    status=work_order.order_status.value
                )
                tasks.append(task)

                all_start_dates.append(task.start_date)
                all_end_dates.append(task.end_date)

        # Detect lane conflicts
        conflicts = []
        if dto.plant_id and dto.start_date and dto.end_date:
            conflicts = self.repo.detect_lane_conflicts(
                plant_id=dto.plant_id,
                start_date=dto.start_date,
                end_date=dto.end_date
            )

        # Calculate critical path (simplified - just find longest sequence)
        critical_path = self._calculate_critical_path(tasks)

        # Mark critical path tasks
        critical_task_ids = set(critical_path)
        for task in tasks:
            if task.work_order_id in critical_task_ids:
                task.is_critical_path = True

        # Calculate overall timeline
        overall_start = min(all_start_dates) if all_start_dates else datetime.now()
        overall_end = max(all_end_dates) if all_end_dates else datetime.now()

        return GanttChartResponse(
            tasks=tasks,
            conflicts=conflicts,
            critical_path=critical_path,
            start_date=overall_start,
            end_date=overall_end,
            total_work_orders=len(work_orders)
        )

    def _calculate_operation_progress(self, work_order: WorkOrder, operation_id: int) -> float:
        """
        Calculate operation progress percentage.

        TODO: Implement based on production logs
        """
        return 0.0

    def _calculate_work_order_progress(self, work_order: WorkOrder) -> float:
        """
        Calculate work order progress percentage.

        Based on quantity_completed / quantity_ordered
        """
        if work_order.quantity_ordered <= 0:
            return 0.0

        return (work_order.quantity_completed / work_order.quantity_ordered) * 100.0

    def _calculate_critical_path(self, tasks: List[GanttChartTask]) -> List[int]:
        """
        Calculate critical path (simplified algorithm).

        Returns list of work order IDs on critical path.

        For full CPM implementation, would need to calculate:
        - Early Start/Finish times
        - Late Start/Finish times
        - Float (slack) for each task
        - Tasks with zero float are on critical path
        """
        if not tasks:
            return []

        # Simplified: Return longest sequence of dependent tasks
        # Group by work order
        wo_tasks = {}
        for task in tasks:
            if task.work_order_id not in wo_tasks:
                wo_tasks[task.work_order_id] = []
            wo_tasks[task.work_order_id].append(task)

        # Find work order with longest duration
        longest_wo = max(wo_tasks.items(), key=lambda x: sum(t.duration_hours for t in x[1]))

        return [longest_wo[0]]
