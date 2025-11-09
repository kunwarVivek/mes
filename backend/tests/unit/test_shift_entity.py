"""
Unit tests for Shift domain entity - TDD RED phase.
Tests business logic and validation rules for shift management.
"""
import pytest
from datetime import datetime, time
from app.domain.entities.shift import ShiftDomain, ShiftHandoverDomain


class TestShiftDomain:
    """Test suite for ShiftDomain entity"""

    def test_create_valid_shift(self):
        """Test creating a valid shift pattern"""
        shift = ShiftDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            shift_name="Morning Shift",
            shift_code="MS",
            start_time=time(6, 0),
            end_time=time(14, 0),
            production_target=100.0,
            is_active=True,
            created_at=None
        )

        assert shift.shift_name == "Morning Shift"
        assert shift.shift_code == "MS"
        assert shift.start_time == time(6, 0)
        assert shift.end_time == time(14, 0)
        assert shift.production_target == 100.0
        assert shift.is_active is True

    def test_shift_code_is_uppercase(self):
        """Test shift code is automatically converted to uppercase"""
        shift = ShiftDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            shift_name="Night Shift",
            shift_code="ns",
            start_time=time(22, 0),
            end_time=time(6, 0),
            production_target=80.0,
        )

        assert shift.shift_code == "NS"

    def test_invalid_organization_id(self):
        """Test validation fails for invalid organization_id"""
        with pytest.raises(ValueError, match="Organization ID must be positive"):
            ShiftDomain(
                id=None,
                organization_id=0,
                plant_id=1,
                shift_name="Morning Shift",
                shift_code="MS",
                start_time=time(6, 0),
                end_time=time(14, 0),
                production_target=100.0,
            )

    def test_invalid_plant_id(self):
        """Test validation fails for invalid plant_id"""
        with pytest.raises(ValueError, match="Plant ID must be positive"):
            ShiftDomain(
                id=None,
                organization_id=1,
                plant_id=-1,
                shift_name="Morning Shift",
                shift_code="MS",
                start_time=time(6, 0),
                end_time=time(14, 0),
                production_target=100.0,
            )

    def test_empty_shift_name(self):
        """Test validation fails for empty shift name"""
        with pytest.raises(ValueError, match="Shift name cannot be empty"):
            ShiftDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                shift_name="",
                shift_code="MS",
                start_time=time(6, 0),
                end_time=time(14, 0),
                production_target=100.0,
            )

    def test_empty_shift_code(self):
        """Test validation fails for empty shift code"""
        with pytest.raises(ValueError, match="Shift code cannot be empty"):
            ShiftDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                shift_name="Morning Shift",
                shift_code="",
                start_time=time(6, 0),
                end_time=time(14, 0),
                production_target=100.0,
            )

    def test_negative_production_target(self):
        """Test validation fails for negative production target"""
        with pytest.raises(ValueError, match="Production target cannot be negative"):
            ShiftDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                shift_name="Morning Shift",
                shift_code="MS",
                start_time=time(6, 0),
                end_time=time(14, 0),
                production_target=-10.0,
            )

    def test_activate_deactivate_shift(self):
        """Test activating and deactivating shift"""
        shift = ShiftDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            shift_name="Morning Shift",
            shift_code="MS",
            start_time=time(6, 0),
            end_time=time(14, 0),
            production_target=100.0,
            is_active=False,
        )

        shift.activate()
        assert shift.is_active is True

        shift.deactivate()
        assert shift.is_active is False

    def test_calculate_shift_duration_hours(self):
        """Test calculating shift duration in hours"""
        shift = ShiftDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            shift_name="Morning Shift",
            shift_code="MS",
            start_time=time(6, 0),
            end_time=time(14, 0),
            production_target=100.0,
        )

        duration = shift.calculate_duration_hours()
        assert duration == 8.0

    def test_calculate_shift_duration_overnight(self):
        """Test calculating shift duration for overnight shifts"""
        shift = ShiftDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            shift_name="Night Shift",
            shift_code="NS",
            start_time=time(22, 0),
            end_time=time(6, 0),
            production_target=80.0,
        )

        duration = shift.calculate_duration_hours()
        assert duration == 8.0


class TestShiftHandoverDomain:
    """Test suite for ShiftHandoverDomain entity"""

    def test_create_valid_handover(self):
        """Test creating a valid shift handover"""
        handover = ShiftHandoverDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            from_shift_id=1,
            to_shift_id=2,
            handover_date=datetime(2025, 1, 8, 14, 0),
            wip_quantity=50.0,
            production_summary="Completed 95 units, 5 in progress",
            quality_issues="2 units rejected due to dimensional defects",
            machine_status="All machines operational",
            material_status="Raw material sufficient for next shift",
            safety_incidents=None,
            handover_by_user_id=1,
            acknowledged_by_user_id=None,
        )

        assert handover.from_shift_id == 1
        assert handover.to_shift_id == 2
        assert handover.wip_quantity == 50.0
        assert handover.production_summary == "Completed 95 units, 5 in progress"
        assert handover.is_acknowledged is False

    def test_invalid_handover_organization_id(self):
        """Test validation fails for invalid organization_id"""
        with pytest.raises(ValueError, match="Organization ID must be positive"):
            ShiftHandoverDomain(
                id=None,
                organization_id=0,
                plant_id=1,
                from_shift_id=1,
                to_shift_id=2,
                handover_date=datetime(2025, 1, 8, 14, 0),
                wip_quantity=50.0,
                production_summary="Test",
                handover_by_user_id=1,
            )

    def test_negative_wip_quantity(self):
        """Test validation fails for negative WIP quantity"""
        with pytest.raises(ValueError, match="WIP quantity cannot be negative"):
            ShiftHandoverDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                from_shift_id=1,
                to_shift_id=2,
                handover_date=datetime(2025, 1, 8, 14, 0),
                wip_quantity=-10.0,
                production_summary="Test",
                handover_by_user_id=1,
            )

    def test_same_shift_handover(self):
        """Test validation fails when from_shift and to_shift are the same"""
        with pytest.raises(ValueError, match="Cannot handover to the same shift"):
            ShiftHandoverDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                from_shift_id=1,
                to_shift_id=1,
                handover_date=datetime(2025, 1, 8, 14, 0),
                wip_quantity=50.0,
                production_summary="Test",
                handover_by_user_id=1,
            )

    def test_acknowledge_handover(self):
        """Test acknowledging a shift handover"""
        handover = ShiftHandoverDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            from_shift_id=1,
            to_shift_id=2,
            handover_date=datetime(2025, 1, 8, 14, 0),
            wip_quantity=50.0,
            production_summary="Test",
            handover_by_user_id=1,
            acknowledged_by_user_id=None,
        )

        assert handover.is_acknowledged is False

        handover.acknowledge(user_id=2)
        assert handover.is_acknowledged is True
        assert handover.acknowledged_by_user_id == 2
        assert handover.acknowledged_at is not None

    def test_cannot_acknowledge_twice(self):
        """Test validation fails when trying to acknowledge already acknowledged handover"""
        handover = ShiftHandoverDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            from_shift_id=1,
            to_shift_id=2,
            handover_date=datetime(2025, 1, 8, 14, 0),
            wip_quantity=50.0,
            production_summary="Test",
            handover_by_user_id=1,
            acknowledged_by_user_id=2,
            acknowledged_at=datetime.utcnow(),
        )

        with pytest.raises(ValueError, match="Handover already acknowledged"):
            handover.acknowledge(user_id=3)
