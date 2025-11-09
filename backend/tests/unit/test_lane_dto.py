"""
Unit tests for Lane DTOs (Pydantic validation)
Testing request/response validation
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

from app.application.dtos.lane_dto import (
    LaneCreateRequest,
    LaneUpdateRequest,
    LaneResponse,
    LaneAssignmentCreateRequest,
    LaneAssignmentUpdateRequest,
    LaneAssignmentResponse,
    LaneCapacityResponse
)
from app.domain.entities.lane import LaneAssignmentStatus


class TestLaneCreateRequest:
    """Test Lane creation DTO validation"""

    def test_valid_lane_create_request(self):
        """Test valid lane creation request"""
        dto = LaneCreateRequest(
            plant_id=1,
            lane_code="L001",
            lane_name="Assembly Line 1",
            capacity_per_day=Decimal("100.500")
        )

        assert dto.plant_id == 1
        assert dto.lane_code == "L001"
        assert dto.lane_name == "Assembly Line 1"
        assert dto.capacity_per_day == Decimal("100.500")

    def test_lane_code_pattern_validation(self):
        """Test lane_code must match pattern"""
        # Valid patterns
        for code in ["L001", "LANE-A", "L_001", "MAIN-LINE-1"]:
            dto = LaneCreateRequest(
                plant_id=1,
                lane_code=code,
                lane_name="Test Lane",
                capacity_per_day=Decimal("100")
            )
            assert dto.lane_code == code

    def test_lane_code_invalid_pattern(self):
        """Test lane_code rejects lowercase and special chars"""
        with pytest.raises(ValidationError):
            LaneCreateRequest(
                plant_id=1,
                lane_code="lane001",  # lowercase not allowed
                lane_name="Test Lane",
                capacity_per_day=Decimal("100")
            )

    def test_plant_id_must_be_positive(self):
        """Test plant_id must be > 0"""
        with pytest.raises(ValidationError):
            LaneCreateRequest(
                plant_id=0,
                lane_code="L001",
                lane_name="Test Lane",
                capacity_per_day=Decimal("100")
            )

    def test_capacity_must_be_positive(self):
        """Test capacity_per_day must be > 0"""
        with pytest.raises(ValidationError):
            LaneCreateRequest(
                plant_id=1,
                lane_code="L001",
                lane_name="Test Lane",
                capacity_per_day=Decimal("0")
            )

    def test_lane_name_max_length(self):
        """Test lane_name cannot exceed 200 characters"""
        with pytest.raises(ValidationError):
            LaneCreateRequest(
                plant_id=1,
                lane_code="L001",
                lane_name="A" * 201,
                capacity_per_day=Decimal("100")
            )


class TestLaneUpdateRequest:
    """Test Lane update DTO validation"""

    def test_valid_lane_update_request(self):
        """Test valid lane update request"""
        dto = LaneUpdateRequest(
            lane_name="Updated Line",
            capacity_per_day=Decimal("150.000"),
            is_active=False
        )

        assert dto.lane_name == "Updated Line"
        assert dto.capacity_per_day == Decimal("150.000")
        assert dto.is_active is False

    def test_partial_update_allowed(self):
        """Test partial updates are allowed"""
        dto = LaneUpdateRequest(lane_name="Updated Name")

        assert dto.lane_name == "Updated Name"
        assert dto.capacity_per_day is None
        assert dto.is_active is None

    def test_capacity_must_be_positive_if_provided(self):
        """Test capacity validation on update"""
        with pytest.raises(ValidationError):
            LaneUpdateRequest(capacity_per_day=Decimal("-10"))


class TestLaneAssignmentCreateRequest:
    """Test Lane Assignment creation DTO validation"""

    def test_valid_assignment_create_request(self):
        """Test valid assignment creation request"""
        dto = LaneAssignmentCreateRequest(
            organization_id=1,
            plant_id=1,
            lane_id=1,
            work_order_id=100,
            project_id=10,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000"),
            priority=1,
            notes="Test assignment"
        )

        assert dto.organization_id == 1
        assert dto.plant_id == 1
        assert dto.lane_id == 1
        assert dto.work_order_id == 100
        assert dto.project_id == 10
        assert dto.scheduled_start == date(2025, 1, 1)
        assert dto.scheduled_end == date(2025, 1, 5)
        assert dto.allocated_capacity == Decimal("50.000")
        assert dto.priority == 1
        assert dto.notes == "Test assignment"

    def test_assignment_with_null_project(self):
        """Test assignment can have null project_id"""
        dto = LaneAssignmentCreateRequest(
            organization_id=1,
            plant_id=1,
            lane_id=1,
            work_order_id=100,
            project_id=None,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000")
        )

        assert dto.project_id is None

    def test_default_priority_is_zero(self):
        """Test priority defaults to 0"""
        dto = LaneAssignmentCreateRequest(
            organization_id=1,
            plant_id=1,
            lane_id=1,
            work_order_id=100,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000")
        )

        assert dto.priority == 0

    def test_priority_cannot_be_negative(self):
        """Test priority must be >= 0"""
        with pytest.raises(ValidationError):
            LaneAssignmentCreateRequest(
                organization_id=1,
                plant_id=1,
                lane_id=1,
                work_order_id=100,
                scheduled_start=date(2025, 1, 1),
                scheduled_end=date(2025, 1, 5),
                allocated_capacity=Decimal("50.000"),
                priority=-1
            )

    def test_allocated_capacity_must_be_positive(self):
        """Test allocated_capacity must be > 0"""
        with pytest.raises(ValidationError):
            LaneAssignmentCreateRequest(
                organization_id=1,
                plant_id=1,
                lane_id=1,
                work_order_id=100,
                scheduled_start=date(2025, 1, 1),
                scheduled_end=date(2025, 1, 5),
                allocated_capacity=Decimal("0")
            )

    def test_all_ids_must_be_positive(self):
        """Test all ID fields must be > 0"""
        with pytest.raises(ValidationError):
            LaneAssignmentCreateRequest(
                organization_id=0,
                plant_id=1,
                lane_id=1,
                work_order_id=100,
                scheduled_start=date(2025, 1, 1),
                scheduled_end=date(2025, 1, 5),
                allocated_capacity=Decimal("50.000")
            )


class TestLaneAssignmentUpdateRequest:
    """Test Lane Assignment update DTO validation"""

    def test_valid_assignment_update_request(self):
        """Test valid assignment update request"""
        dto = LaneAssignmentUpdateRequest(
            scheduled_start=date(2025, 1, 2),
            scheduled_end=date(2025, 1, 6),
            allocated_capacity=Decimal("60.000"),
            priority=2,
            status=LaneAssignmentStatus.ACTIVE,
            notes="Updated assignment"
        )

        assert dto.scheduled_start == date(2025, 1, 2)
        assert dto.scheduled_end == date(2025, 1, 6)
        assert dto.allocated_capacity == Decimal("60.000")
        assert dto.priority == 2
        assert dto.status == LaneAssignmentStatus.ACTIVE
        assert dto.notes == "Updated assignment"

    def test_partial_update_allowed(self):
        """Test partial updates are allowed"""
        dto = LaneAssignmentUpdateRequest(status=LaneAssignmentStatus.COMPLETED)

        assert dto.status == LaneAssignmentStatus.COMPLETED
        assert dto.scheduled_start is None
        assert dto.allocated_capacity is None

    def test_capacity_must_be_positive_if_provided(self):
        """Test capacity validation on update"""
        with pytest.raises(ValidationError):
            LaneAssignmentUpdateRequest(allocated_capacity=Decimal("-10"))

    def test_priority_cannot_be_negative_if_provided(self):
        """Test priority validation on update"""
        with pytest.raises(ValidationError):
            LaneAssignmentUpdateRequest(priority=-1)


class TestLaneCapacityResponse:
    """Test Lane Capacity response DTO"""

    def test_valid_capacity_response(self):
        """Test valid capacity response"""
        dto = LaneCapacityResponse(
            lane_id=1,
            date=date(2025, 1, 1),
            total_capacity=Decimal("100.000"),
            allocated_capacity=Decimal("75.000"),
            available_capacity=Decimal("25.000"),
            utilization_rate=Decimal("75.00"),
            assignment_count=3
        )

        assert dto.lane_id == 1
        assert dto.date == date(2025, 1, 1)
        assert dto.total_capacity == Decimal("100.000")
        assert dto.allocated_capacity == Decimal("75.000")
        assert dto.available_capacity == Decimal("25.000")
        assert dto.utilization_rate == Decimal("75.00")
        assert dto.assignment_count == 3
