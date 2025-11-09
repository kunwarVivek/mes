"""
Lane Repository - Data access layer for lanes and lane assignments
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import date
from decimal import Decimal

from app.models.lane import Lane, LaneAssignment
from app.application.dtos.lane_dto import (
    LaneCreateRequest,
    LaneUpdateRequest,
    LaneAssignmentCreateRequest,
    LaneAssignmentUpdateRequest,
    LaneCapacityResponse
)
from app.domain.entities.lane import LaneAssignmentStatus


class LaneRepository:
    """Repository for Lane and Lane Assignment database operations"""

    def __init__(self, db: Session):
        self.db = db

    # Lane CRUD operations
    def create_lane(self, dto: LaneCreateRequest) -> Lane:
        """
        Create a new lane

        Args:
            dto: Lane creation request

        Returns:
            Created Lane model

        Raises:
            ValueError: If lane_code already exists in plant
        """
        # Check for duplicate lane_code in same plant
        existing = self.db.query(Lane).filter(
            Lane.plant_id == dto.plant_id,
            Lane.lane_code == dto.lane_code
        ).first()

        if existing:
            raise ValueError(f"Lane code {dto.lane_code} already exists in plant {dto.plant_id}")

        lane = Lane(**dto.model_dump())
        self.db.add(lane)
        self.db.commit()
        self.db.refresh(lane)
        return lane

    def get_lane_by_id(self, lane_id: int) -> Optional[Lane]:
        """
        Get a single lane by ID

        Args:
            lane_id: Lane ID

        Returns:
            Lane model or None if not found
        """
        return self.db.query(Lane).filter(Lane.id == lane_id).first()

    def list_lanes(
        self,
        plant_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """
        List lanes with optional filters and pagination

        Args:
            plant_id: Filter by plant ID
            is_active: Filter by active status
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with items, total, page, page_size
        """
        query = self.db.query(Lane)

        if plant_id is not None:
            query = query.filter(Lane.plant_id == plant_id)

        if is_active is not None:
            query = query.filter(Lane.is_active == is_active)

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def update_lane(self, lane_id: int, dto: LaneUpdateRequest) -> Optional[Lane]:
        """
        Update a lane

        Args:
            lane_id: Lane ID
            dto: Update request with fields to update

        Returns:
            Updated Lane model or None if not found
        """
        lane = self.get_lane_by_id(lane_id)
        if not lane:
            return None

        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(lane, field, value)

        self.db.commit()
        self.db.refresh(lane)
        return lane

    def delete_lane(self, lane_id: int) -> bool:
        """
        Soft delete a lane (set is_active = False)

        Args:
            lane_id: Lane ID

        Returns:
            True if deleted, False if not found
        """
        lane = self.get_lane_by_id(lane_id)
        if not lane:
            return False

        lane.is_active = False
        self.db.commit()
        return True

    # Lane Assignment CRUD operations
    def create_assignment(self, dto: LaneAssignmentCreateRequest) -> LaneAssignment:
        """
        Create a new lane assignment with capacity validation

        Args:
            dto: Assignment creation request

        Returns:
            Created LaneAssignment model

        Raises:
            ValueError: If lane not found or capacity exceeds lane capacity
        """
        # Validate lane exists
        lane = self.get_lane_by_id(dto.lane_id)
        if not lane:
            raise ValueError(f"Lane {dto.lane_id} not found")

        # Validate allocated capacity doesn't exceed lane daily capacity
        if dto.allocated_capacity > lane.capacity_per_day:
            raise ValueError(
                f"Allocated capacity {dto.allocated_capacity} exceeds lane daily capacity {lane.capacity_per_day}"
            )

        assignment = LaneAssignment(**dto.model_dump())
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_assignment_by_id(self, assignment_id: int) -> Optional[LaneAssignment]:
        """
        Get a single assignment by ID

        Args:
            assignment_id: Assignment ID

        Returns:
            LaneAssignment model or None if not found
        """
        return self.db.query(LaneAssignment).filter(LaneAssignment.id == assignment_id).first()

    def list_assignments(
        self,
        lane_id: Optional[int] = None,
        plant_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[LaneAssignmentStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> dict:
        """
        List lane assignments with optional filters and pagination

        Args:
            lane_id: Filter by lane ID
            plant_id: Filter by plant ID
            start_date: Filter assignments ending on or after this date
            end_date: Filter assignments starting on or before this date
            status: Filter by status
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with items, total, page, page_size
        """
        query = self.db.query(LaneAssignment)

        if lane_id is not None:
            query = query.filter(LaneAssignment.lane_id == lane_id)

        if plant_id is not None:
            query = query.filter(LaneAssignment.plant_id == plant_id)

        if start_date is not None:
            query = query.filter(LaneAssignment.scheduled_end >= start_date)

        if end_date is not None:
            query = query.filter(LaneAssignment.scheduled_start <= end_date)

        if status is not None:
            query = query.filter(LaneAssignment.status == status)

        total = query.count()
        items = query.order_by(LaneAssignment.scheduled_start).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def update_assignment(self, assignment_id: int, dto: LaneAssignmentUpdateRequest) -> Optional[LaneAssignment]:
        """
        Update a lane assignment

        Args:
            assignment_id: Assignment ID
            dto: Update request with fields to update

        Returns:
            Updated LaneAssignment model or None if not found
        """
        assignment = self.get_assignment_by_id(assignment_id)
        if not assignment:
            return None

        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(assignment, field, value)

        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def delete_assignment(self, assignment_id: int) -> bool:
        """
        Delete a lane assignment (hard delete)

        Args:
            assignment_id: Assignment ID

        Returns:
            True if deleted, False if not found
        """
        assignment = self.get_assignment_by_id(assignment_id)
        if not assignment:
            return False

        self.db.delete(assignment)
        self.db.commit()
        return True

    def get_lane_capacity(self, lane_id: int, target_date: date) -> Optional[LaneCapacityResponse]:
        """
        Get capacity utilization for a lane on a specific date

        Args:
            lane_id: Lane ID
            target_date: Date to check capacity for

        Returns:
            LaneCapacityResponse with capacity details or None if lane not found
        """
        lane = self.get_lane_by_id(lane_id)
        if not lane:
            return None

        # Sum allocated capacity for all assignments that overlap the target date
        # Only include PLANNED and ACTIVE assignments
        result = self.db.query(
            func.sum(LaneAssignment.allocated_capacity).label('allocated'),
            func.count(LaneAssignment.id).label('count')
        ).filter(
            LaneAssignment.lane_id == lane_id,
            LaneAssignment.scheduled_start <= target_date,
            LaneAssignment.scheduled_end >= target_date,
            LaneAssignment.status.in_([LaneAssignmentStatus.PLANNED, LaneAssignmentStatus.ACTIVE])
        ).first()

        allocated = result.allocated or Decimal("0")
        available = lane.capacity_per_day - allocated
        utilization = (allocated / lane.capacity_per_day * 100) if lane.capacity_per_day > 0 else Decimal("0")

        return LaneCapacityResponse(
            lane_id=lane_id,
            date=target_date,
            total_capacity=lane.capacity_per_day,
            allocated_capacity=allocated,
            available_capacity=available,
            utilization_rate=utilization.quantize(Decimal("0.01")),
            assignment_count=result.count or 0
        )
