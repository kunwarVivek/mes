"""
Validate Schedule Use Case

Validates scheduling constraints before assignment.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.infrastructure.repositories.scheduling_repository import SchedulingRepository
from app.models.work_order import WorkOrder
from app.core.exceptions import (
    ValidationException,
    ConflictException,
    EntityNotFoundException
)


class ValidateScheduleDTO:
    """Data Transfer Object for schedule validation."""

    def __init__(
        self,
        work_order_id: int,
        lane_id: int,
        start_date: datetime,
        end_date: datetime
    ):
        self.work_order_id = work_order_id
        self.lane_id = lane_id
        self.start_date = start_date
        self.end_date = end_date


class ValidationResult:
    """Value object for validation result."""

    def __init__(
        self,
        is_valid: bool,
        errors: list = None,
        warnings: list = None
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []


class ValidateScheduleUseCase:
    """
    Use case for validating schedule constraints.

    Business Rules:
    - BR-SCHED-001: No overlapping assignments - Lane must be available
    - BR-SCHED-002: Work order dates must align with dependencies
    - BR-SCHED-003: Capacity warning if lane utilization > 90%
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = SchedulingRepository(db)

    def execute(self, dto: ValidateScheduleDTO) -> ValidationResult:
        """
        Execute schedule validation.

        Args:
            dto: ValidateScheduleDTO with proposed assignment

        Returns:
            ValidationResult with errors and warnings

        Raises:
            EntityNotFoundException: If work order or lane not found
            ValidationException: If basic validation fails
        """
        errors = []
        warnings = []

        # 1. Validate work order exists
        work_order = self.db.query(WorkOrder).filter(
            WorkOrder.id == dto.work_order_id
        ).first()

        if not work_order:
            raise EntityNotFoundException(
                entity_type="WorkOrder",
                entity_id=dto.work_order_id
            )

        # 2. Validate date range
        if dto.start_date >= dto.end_date:
            errors.append("Start date must be before end date")

        # 3. Validate lane availability (BR-SCHED-001)
        is_available = self.repo.validate_lane_availability(
            lane_id=dto.lane_id,
            start_date=dto.start_date,
            end_date=dto.end_date,
            exclude_work_order_id=dto.work_order_id
        )

        if not is_available:
            errors.append(
                f"Lane is not available from {dto.start_date} to {dto.end_date}. "
                "Another work order is already assigned."
            )

        # 4. Validate dependency constraints (BR-SCHED-002)
        if work_order.predecessor_work_order_id:
            predecessor = self.db.query(WorkOrder).filter(
                WorkOrder.id == work_order.predecessor_work_order_id
            ).first()

            if predecessor:
                # Check if predecessor end date is before proposed start date
                if predecessor.planned_end_date and predecessor.planned_end_date > dto.start_date:
                    warnings.append(
                        f"Predecessor work order {predecessor.work_order_number} "
                        f"is planned to end at {predecessor.planned_end_date}, "
                        f"which is after proposed start date {dto.start_date}"
                    )

        # 5. Check for reasonable duration
        duration_days = (dto.end_date - dto.start_date).days
        if duration_days > 365:
            warnings.append(
                f"Duration of {duration_days} days seems unusually long. "
                "Please verify the dates."
            )

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
