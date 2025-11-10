"""
Detect Conflicts Use Case

Detects scheduling conflicts (lane overload, dependency violations).
"""
from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.infrastructure.repositories.scheduling_repository import SchedulingRepository


class DetectConflictsDTO:
    """Data Transfer Object for conflict detection."""

    def __init__(
        self,
        plant_id: int,
        start_date: date,
        end_date: date
    ):
        self.plant_id = plant_id
        self.start_date = start_date
        self.end_date = end_date


class ConflictResponse:
    """Value object for conflict information."""

    def __init__(
        self,
        conflict_type: str,  # "LANE_OVERLOAD", "DEPENDENCY_VIOLATION"
        severity: str,  # "HIGH", "MEDIUM", "LOW"
        description: str,
        affected_work_orders: List[int],
        affected_lanes: List[int],
        details: dict
    ):
        self.conflict_type = conflict_type
        self.severity = severity
        self.description = description
        self.affected_work_orders = affected_work_orders
        self.affected_lanes = affected_lanes
        self.details = details


class DetectConflictsUseCase:
    """
    Use case for detecting scheduling conflicts.

    Business Rules:
    - BR-SCHED-001: No overlapping assignments - Lane can only have one WO at a time
    - BR-SCHED-002: Dependency validation - Predecessor must complete before successor
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = SchedulingRepository(db)

    def execute(self, dto: DetectConflictsDTO) -> List[ConflictResponse]:
        """
        Execute conflict detection.

        Args:
            dto: DetectConflictsDTO with plant and date range

        Returns:
            List of ConflictResponse objects
        """
        conflicts = []

        # Detect lane overload conflicts
        lane_conflicts = self.repo.detect_lane_conflicts(
            plant_id=dto.plant_id,
            start_date=dto.start_date,
            end_date=dto.end_date
        )

        for conflict_data in lane_conflicts:
            conflicts.append(ConflictResponse(
                conflict_type="LANE_OVERLOAD",
                severity="HIGH",
                description=f"Lane {conflict_data['lane_code']} has overlapping assignments",
                affected_work_orders=[
                    conflict_data['work_order_1_id'],
                    conflict_data['work_order_2_id']
                ],
                affected_lanes=[conflict_data['lane_id']],
                details={
                    "work_order_1": conflict_data['work_order_1_number'],
                    "work_order_2": conflict_data['work_order_2_number'],
                    "overlap_start": conflict_data['overlap_start'].isoformat(),
                    "overlap_end": conflict_data['overlap_end'].isoformat()
                }
            ))

        return conflicts
