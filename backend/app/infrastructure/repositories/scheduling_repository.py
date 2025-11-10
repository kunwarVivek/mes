"""
Scheduling Repository

Provides data access methods for work orders, lanes, and scheduling operations.
"""
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from app.models.work_order import WorkOrder, OrderStatus
from app.models.lane import Lane, LaneAssignment


class SchedulingRepository:
    """
    Repository for scheduling-related queries.

    Provides optimized queries for Gantt chart data retrieval.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_work_orders_for_gantt(
        self,
        plant_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        lane_ids: Optional[List[int]] = None,
        include_completed: bool = False,
        organization_id: Optional[int] = None
    ) -> List[WorkOrder]:
        """
        Get work orders for Gantt chart visualization.

        Args:
            plant_id: Filter by plant
            start_date: Filter by planned_start_date >= start_date
            end_date: Filter by planned_end_date <= end_date
            lane_ids: Filter by lane assignments
            include_completed: Include completed work orders
            organization_id: Filter by organization (for RLS)

        Returns:
            List of work orders with eager-loaded operations and lanes
        """
        query = self.db.query(WorkOrder).options(
            joinedload(WorkOrder.operations),
            joinedload(WorkOrder.lane_assignments)
        )

        # Filter by organization (RLS enforced at database level, but add for clarity)
        if organization_id:
            query = query.filter(WorkOrder.organization_id == organization_id)

        # Filter by plant
        if plant_id:
            query = query.filter(WorkOrder.plant_id == plant_id)

        # Filter by date range
        if start_date:
            query = query.filter(WorkOrder.planned_start_date >= start_date)

        if end_date:
            query = query.filter(WorkOrder.planned_end_date <= end_date)

        # Filter by status
        if not include_completed:
            query = query.filter(
                WorkOrder.order_status.in_([
                    OrderStatus.PLANNED,
                    OrderStatus.RELEASED,
                    OrderStatus.IN_PROGRESS
                ])
            )

        # Filter by lanes
        if lane_ids:
            query = query.join(LaneAssignment).filter(
                LaneAssignment.lane_id.in_(lane_ids)
            )

        return query.all()

    def get_lanes(
        self,
        plant_id: Optional[int] = None,
        is_active: bool = True
    ) -> List[Lane]:
        """
        Get lanes for a plant.

        Args:
            plant_id: Filter by plant
            is_active: Filter by active status

        Returns:
            List of lanes
        """
        query = self.db.query(Lane)

        if plant_id:
            query = query.filter(Lane.plant_id == plant_id)

        if is_active is not None:
            query = query.filter(Lane.is_active == is_active)

        return query.all()

    def get_lane_assignments_in_period(
        self,
        lane_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[LaneAssignment]:
        """
        Get lane assignments that overlap with given time period.

        Used for conflict detection (lane overload).

        Args:
            lane_id: Lane ID
            start_date: Period start
            end_date: Period end

        Returns:
            List of lane assignments in the period
        """
        query = self.db.query(LaneAssignment).filter(
            and_(
                LaneAssignment.lane_id == lane_id,
                # Check for overlap: (start1 <= end2) AND (end1 >= start2)
                LaneAssignment.start_date <= end_date,
                LaneAssignment.end_date >= start_date
            )
        )

        return query.all()

    def detect_lane_conflicts(
        self,
        plant_id: int,
        start_date: date,
        end_date: date
    ) -> List[dict]:
        """
        Detect lane conflicts (multiple work orders assigned to same lane at same time).

        Args:
            plant_id: Plant ID
            start_date: Period start
            end_date: Period end

        Returns:
            List of conflicts with lane_id, work_order_ids, overlap dates
        """
        # Query for overlapping lane assignments
        assignments = self.db.query(LaneAssignment).join(Lane).filter(
            and_(
                Lane.plant_id == plant_id,
                LaneAssignment.start_date <= end_date,
                LaneAssignment.end_date >= start_date
            )
        ).all()

        # Group by lane and find overlaps
        lane_assignments = {}
        for assignment in assignments:
            lane_id = assignment.lane_id
            if lane_id not in lane_assignments:
                lane_assignments[lane_id] = []
            lane_assignments[lane_id].append(assignment)

        # Detect conflicts
        conflicts = []
        for lane_id, assignments_list in lane_assignments.items():
            # Check each pair for overlap
            for i, a1 in enumerate(assignments_list):
                for a2 in assignments_list[i+1:]:
                    # Check if they overlap
                    if self._assignments_overlap(a1, a2):
                        conflicts.append({
                            'lane_id': lane_id,
                            'lane_code': a1.lane.lane_code if a1.lane else None,
                            'work_order_1_id': a1.work_order_id,
                            'work_order_1_number': a1.work_order.work_order_number if a1.work_order else None,
                            'work_order_2_id': a2.work_order_id,
                            'work_order_2_number': a2.work_order.work_order_number if a2.work_order else None,
                            'overlap_start': max(a1.start_date, a2.start_date),
                            'overlap_end': min(a1.end_date, a2.end_date)
                        })

        return conflicts

    def _assignments_overlap(self, a1: LaneAssignment, a2: LaneAssignment) -> bool:
        """
        Check if two lane assignments overlap in time.

        Two intervals overlap if: (start1 <= end2) AND (end1 >= start2)
        """
        return (a1.start_date <= a2.end_date) and (a1.end_date >= a2.start_date)

    def get_work_order_dependencies(
        self,
        work_order_id: int
    ) -> List[WorkOrder]:
        """
        Get all work orders that the given work order depends on.

        Args:
            work_order_id: Work order ID

        Returns:
            List of dependent work orders
        """
        work_order = self.db.query(WorkOrder).filter(
            WorkOrder.id == work_order_id
        ).first()

        if not work_order or not work_order.predecessor_work_order_id:
            return []

        # For now, return immediate predecessor
        # In future, could implement recursive dependency tree
        predecessor = self.db.query(WorkOrder).filter(
            WorkOrder.id == work_order.predecessor_work_order_id
        ).first()

        return [predecessor] if predecessor else []

    def validate_lane_availability(
        self,
        lane_id: int,
        start_date: datetime,
        end_date: datetime,
        exclude_work_order_id: Optional[int] = None
    ) -> bool:
        """
        Check if lane is available during given time period.

        Args:
            lane_id: Lane ID
            start_date: Proposed start date
            end_date: Proposed end date
            exclude_work_order_id: Exclude this work order from conflict check (for updates)

        Returns:
            True if available, False if conflict exists
        """
        query = self.db.query(LaneAssignment).filter(
            and_(
                LaneAssignment.lane_id == lane_id,
                LaneAssignment.start_date <= end_date,
                LaneAssignment.end_date >= start_date
            )
        )

        if exclude_work_order_id:
            query = query.filter(LaneAssignment.work_order_id != exclude_work_order_id)

        conflicts = query.all()
        return len(conflicts) == 0
