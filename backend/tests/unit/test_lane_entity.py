"""
Unit tests for Lane domain entities
Testing business logic and validation rules
"""
import pytest
from datetime import datetime, date
from decimal import Decimal

from app.domain.entities.lane import (
    LaneDomain,
    LaneAssignmentDomain,
    LaneAssignmentStatus
)


class TestLaneDomain:
    """Test Lane domain entity validation and business logic"""

    def test_create_valid_lane(self):
        """Test creating a valid lane"""
        lane = LaneDomain(
            id=1,
            plant_id=1,
            lane_code="L001",
            lane_name="Assembly Line 1",
            capacity_per_day=Decimal("100.000"),
            is_active=True,
            created_at=datetime.now()
        )

        assert lane.id == 1
        assert lane.plant_id == 1
        assert lane.lane_code == "L001"
        assert lane.lane_name == "Assembly Line 1"
        assert lane.capacity_per_day == Decimal("100.000")
        assert lane.is_active is True

    def test_lane_code_cannot_be_empty(self):
        """Test that lane_code cannot be empty"""
        with pytest.raises(ValueError, match="lane_code must be 1-50 characters"):
            LaneDomain(
                id=1,
                plant_id=1,
                lane_code="",
                lane_name="Assembly Line 1",
                capacity_per_day=Decimal("100.000"),
                is_active=True,
                created_at=datetime.now()
            )

    def test_lane_code_max_length(self):
        """Test lane_code maximum length validation"""
        with pytest.raises(ValueError, match="lane_code must be 1-50 characters"):
            LaneDomain(
                id=1,
                plant_id=1,
                lane_code="A" * 51,
                lane_name="Assembly Line 1",
                capacity_per_day=Decimal("100.000"),
                is_active=True,
                created_at=datetime.now()
            )

    def test_lane_name_cannot_be_empty(self):
        """Test that lane_name cannot be empty"""
        with pytest.raises(ValueError, match="lane_name must be 1-200 characters"):
            LaneDomain(
                id=1,
                plant_id=1,
                lane_code="L001",
                lane_name="",
                capacity_per_day=Decimal("100.000"),
                is_active=True,
                created_at=datetime.now()
            )

    def test_lane_name_max_length(self):
        """Test lane_name maximum length validation"""
        with pytest.raises(ValueError, match="lane_name must be 1-200 characters"):
            LaneDomain(
                id=1,
                plant_id=1,
                lane_code="L001",
                lane_name="A" * 201,
                capacity_per_day=Decimal("100.000"),
                is_active=True,
                created_at=datetime.now()
            )

    def test_capacity_must_be_positive(self):
        """Test that capacity_per_day must be positive"""
        with pytest.raises(ValueError, match="capacity_per_day must be positive"):
            LaneDomain(
                id=1,
                plant_id=1,
                lane_code="L001",
                lane_name="Assembly Line 1",
                capacity_per_day=Decimal("0"),
                is_active=True,
                created_at=datetime.now()
            )

    def test_capacity_cannot_be_negative(self):
        """Test that capacity_per_day cannot be negative"""
        with pytest.raises(ValueError, match="capacity_per_day must be positive"):
            LaneDomain(
                id=1,
                plant_id=1,
                lane_code="L001",
                lane_name="Assembly Line 1",
                capacity_per_day=Decimal("-10.000"),
                is_active=True,
                created_at=datetime.now()
            )


class TestLaneAssignmentDomain:
    """Test Lane Assignment domain entity validation and business logic"""

    def test_create_valid_assignment(self):
        """Test creating a valid lane assignment"""
        assignment = LaneAssignmentDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            lane_id=1,
            work_order_id=100,
            project_id=10,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000"),
            priority=1,
            status=LaneAssignmentStatus.PLANNED,
            notes="Test assignment",
            created_at=datetime.now()
        )

        assert assignment.id == 1
        assert assignment.organization_id == 1
        assert assignment.plant_id == 1
        assert assignment.lane_id == 1
        assert assignment.work_order_id == 100
        assert assignment.project_id == 10
        assert assignment.scheduled_start == date(2025, 1, 1)
        assert assignment.scheduled_end == date(2025, 1, 5)
        assert assignment.allocated_capacity == Decimal("50.000")
        assert assignment.priority == 1
        assert assignment.status == LaneAssignmentStatus.PLANNED
        assert assignment.notes == "Test assignment"

    def test_end_date_must_be_after_or_equal_start_date(self):
        """Test that scheduled_end must be >= scheduled_start"""
        with pytest.raises(ValueError, match="scheduled_end must be >= scheduled_start"):
            LaneAssignmentDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                lane_id=1,
                work_order_id=100,
                project_id=None,
                scheduled_start=date(2025, 1, 5),
                scheduled_end=date(2025, 1, 1),
                allocated_capacity=Decimal("50.000"),
                priority=0,
                status=LaneAssignmentStatus.PLANNED,
                notes=None,
                created_at=datetime.now()
            )

    def test_allocated_capacity_must_be_positive(self):
        """Test that allocated_capacity must be positive"""
        with pytest.raises(ValueError, match="allocated_capacity must be positive"):
            LaneAssignmentDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                lane_id=1,
                work_order_id=100,
                project_id=None,
                scheduled_start=date(2025, 1, 1),
                scheduled_end=date(2025, 1, 5),
                allocated_capacity=Decimal("0"),
                priority=0,
                status=LaneAssignmentStatus.PLANNED,
                notes=None,
                created_at=datetime.now()
            )

    def test_allocated_capacity_cannot_be_negative(self):
        """Test that allocated_capacity cannot be negative"""
        with pytest.raises(ValueError, match="allocated_capacity must be positive"):
            LaneAssignmentDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                lane_id=1,
                work_order_id=100,
                project_id=None,
                scheduled_start=date(2025, 1, 1),
                scheduled_end=date(2025, 1, 5),
                allocated_capacity=Decimal("-10.000"),
                priority=0,
                status=LaneAssignmentStatus.PLANNED,
                notes=None,
                created_at=datetime.now()
            )

    def test_duration_days_calculation(self):
        """Test duration_days property calculation"""
        assignment = LaneAssignmentDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            lane_id=1,
            work_order_id=100,
            project_id=None,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000"),
            priority=0,
            status=LaneAssignmentStatus.PLANNED,
            notes=None,
            created_at=datetime.now()
        )

        # 5 days inclusive (Jan 1-5)
        assert assignment.duration_days == 5

    def test_duration_days_single_day(self):
        """Test duration_days for single day assignment"""
        assignment = LaneAssignmentDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            lane_id=1,
            work_order_id=100,
            project_id=None,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 1),
            allocated_capacity=Decimal("50.000"),
            priority=0,
            status=LaneAssignmentStatus.PLANNED,
            notes=None,
            created_at=datetime.now()
        )

        # Same day = 1 day
        assert assignment.duration_days == 1

    def test_total_capacity_needed_calculation(self):
        """Test total_capacity_needed property calculation"""
        assignment = LaneAssignmentDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            lane_id=1,
            work_order_id=100,
            project_id=None,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000"),
            priority=0,
            status=LaneAssignmentStatus.PLANNED,
            notes=None,
            created_at=datetime.now()
        )

        # 5 days * 50 capacity = 250 total
        assert assignment.total_capacity_needed == Decimal("250.000")

    def test_assignment_with_null_project(self):
        """Test assignment can have null project_id"""
        assignment = LaneAssignmentDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            lane_id=1,
            work_order_id=100,
            project_id=None,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000"),
            priority=0,
            status=LaneAssignmentStatus.PLANNED,
            notes=None,
            created_at=datetime.now()
        )

        assert assignment.project_id is None

    def test_all_assignment_statuses(self):
        """Test all valid assignment statuses"""
        for status in [LaneAssignmentStatus.PLANNED, LaneAssignmentStatus.ACTIVE,
                       LaneAssignmentStatus.COMPLETED, LaneAssignmentStatus.CANCELLED]:
            assignment = LaneAssignmentDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                lane_id=1,
                work_order_id=100,
                project_id=None,
                scheduled_start=date(2025, 1, 1),
                scheduled_end=date(2025, 1, 5),
                allocated_capacity=Decimal("50.000"),
                priority=0,
                status=status,
                notes=None,
                created_at=datetime.now()
            )

            assert assignment.status == status
