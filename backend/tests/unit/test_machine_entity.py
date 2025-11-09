"""
Unit tests for Machine domain entities.

Test Coverage:
- MachineDomain: Status transitions, validation, OEE calculation
- MachineStatusHistoryDomain: Status tracking, duration calculations
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal


class TestMachineDomain:
    """Test Machine domain entity business logic"""

    def test_create_machine_with_valid_data(self):
        """Should create machine with valid data"""
        from app.domain.entities.machine import MachineDomain, MachineStatus

        machine = MachineDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            machine_code="M001",
            machine_name="CNC Machine 1",
            description="CNC Milling Machine",
            work_center_id=1,
            status=MachineStatus.AVAILABLE,
            is_active=True
        )

        assert machine.machine_code == "M001"
        assert machine.machine_name == "CNC Machine 1"
        assert machine.status == MachineStatus.AVAILABLE
        assert machine.is_active is True

    def test_machine_code_validation_alphanumeric(self):
        """Should validate machine code is alphanumeric and max 20 chars"""
        from app.domain.entities.machine import MachineDomain, MachineStatus

        with pytest.raises(ValueError, match="Machine code must be alphanumeric"):
            MachineDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                machine_code="M-001!",  # Invalid characters
                machine_name="CNC Machine",
                description="",
                work_center_id=1,
                status=MachineStatus.AVAILABLE
            )

    def test_machine_code_max_length(self):
        """Should enforce machine code max length of 20 characters"""
        from app.domain.entities.machine import MachineDomain, MachineStatus

        with pytest.raises(ValueError, match="cannot exceed 20 characters"):
            MachineDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                machine_code="A" * 21,  # Too long
                machine_name="CNC Machine",
                description="",
                work_center_id=1,
                status=MachineStatus.AVAILABLE
            )

    def test_organization_id_must_be_positive(self):
        """Should validate organization_id is positive"""
        from app.domain.entities.machine import MachineDomain, MachineStatus

        with pytest.raises(ValueError, match="Organization ID must be positive"):
            MachineDomain(
                id=None,
                organization_id=0,  # Invalid
                plant_id=1,
                machine_code="M001",
                machine_name="CNC Machine",
                description="",
                work_center_id=1,
                status=MachineStatus.AVAILABLE
            )

    def test_machine_status_transition_to_running(self):
        """Should transition machine status from AVAILABLE to RUNNING"""
        from app.domain.entities.machine import MachineDomain, MachineStatus

        machine = MachineDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            machine_code="M001",
            machine_name="CNC Machine",
            description="",
            work_center_id=1,
            status=MachineStatus.AVAILABLE
        )

        machine.change_status(MachineStatus.RUNNING)
        assert machine.status == MachineStatus.RUNNING

    def test_machine_status_transition_to_maintenance(self):
        """Should transition machine to MAINTENANCE status"""
        from app.domain.entities.machine import MachineDomain, MachineStatus

        machine = MachineDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            machine_code="M001",
            machine_name="CNC Machine",
            description="",
            work_center_id=1,
            status=MachineStatus.RUNNING
        )

        machine.change_status(MachineStatus.MAINTENANCE)
        assert machine.status == MachineStatus.MAINTENANCE

    def test_activate_deactivate_machine(self):
        """Should activate and deactivate machine"""
        from app.domain.entities.machine import MachineDomain, MachineStatus

        machine = MachineDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            machine_code="M001",
            machine_name="CNC Machine",
            description="",
            work_center_id=1,
            status=MachineStatus.AVAILABLE
        )

        machine.deactivate()
        assert machine.is_active is False

        machine.activate()
        assert machine.is_active is True


class TestOEECalculation:
    """Test OEE (Overall Equipment Effectiveness) calculation logic"""

    def test_calculate_oee_perfect_performance(self):
        """Should calculate 100% OEE for perfect performance"""
        from app.domain.entities.machine import OEECalculator

        # 8 hour shift, all running time, no defects
        total_time_minutes = 480
        downtime_minutes = 0
        ideal_cycle_time = 1.0  # 1 minute per piece
        total_pieces = 480
        defect_pieces = 0

        oee = OEECalculator.calculate_oee(
            total_time_minutes=total_time_minutes,
            downtime_minutes=downtime_minutes,
            ideal_cycle_time=ideal_cycle_time,
            total_pieces=total_pieces,
            defect_pieces=defect_pieces
        )

        assert oee.availability == pytest.approx(1.0, rel=1e-9)
        assert oee.performance == pytest.approx(1.0, rel=1e-9)
        assert oee.quality == pytest.approx(1.0, rel=1e-9)
        assert oee.oee_score == pytest.approx(1.0, rel=1e-9)

    def test_calculate_oee_with_downtime(self):
        """Should calculate availability correctly with downtime"""
        from app.domain.entities.machine import OEECalculator

        # 8 hour shift, 1 hour downtime = 87.5% availability
        total_time_minutes = 480
        downtime_minutes = 60
        ideal_cycle_time = 1.0
        total_pieces = 420  # 7 hours worth
        defect_pieces = 0

        oee = OEECalculator.calculate_oee(
            total_time_minutes=total_time_minutes,
            downtime_minutes=downtime_minutes,
            ideal_cycle_time=ideal_cycle_time,
            total_pieces=total_pieces,
            defect_pieces=defect_pieces
        )

        expected_availability = (480 - 60) / 480  # 0.875
        assert oee.availability == pytest.approx(expected_availability, rel=1e-9)
        assert oee.performance == pytest.approx(1.0, rel=1e-9)
        assert oee.quality == pytest.approx(1.0, rel=1e-9)
        assert oee.oee_score == pytest.approx(expected_availability, rel=1e-9)

    def test_calculate_oee_with_performance_loss(self):
        """Should calculate performance correctly when running slower than ideal"""
        from app.domain.entities.machine import OEECalculator

        # 8 hour shift, no downtime, but only produced 400 pieces (should be 480)
        total_time_minutes = 480
        downtime_minutes = 0
        ideal_cycle_time = 1.0
        total_pieces = 400  # 83.33% performance
        defect_pieces = 0

        oee = OEECalculator.calculate_oee(
            total_time_minutes=total_time_minutes,
            downtime_minutes=downtime_minutes,
            ideal_cycle_time=ideal_cycle_time,
            total_pieces=total_pieces,
            defect_pieces=defect_pieces
        )

        expected_performance = (400 * 1.0) / 480  # 0.8333
        assert oee.availability == pytest.approx(1.0, rel=1e-9)
        assert oee.performance == pytest.approx(expected_performance, rel=1e-9)
        assert oee.quality == pytest.approx(1.0, rel=1e-9)
        assert oee.oee_score == pytest.approx(expected_performance, rel=1e-9)

    def test_calculate_oee_with_quality_loss(self):
        """Should calculate quality correctly with defects"""
        from app.domain.entities.machine import OEECalculator

        # 8 hour shift, produced 480 pieces, 48 defects = 90% quality
        total_time_minutes = 480
        downtime_minutes = 0
        ideal_cycle_time = 1.0
        total_pieces = 480
        defect_pieces = 48

        oee = OEECalculator.calculate_oee(
            total_time_minutes=total_time_minutes,
            downtime_minutes=downtime_minutes,
            ideal_cycle_time=ideal_cycle_time,
            total_pieces=total_pieces,
            defect_pieces=defect_pieces
        )

        expected_quality = (480 - 48) / 480  # 0.9
        assert oee.availability == pytest.approx(1.0, rel=1e-9)
        assert oee.performance == pytest.approx(1.0, rel=1e-9)
        assert oee.quality == pytest.approx(expected_quality, rel=1e-9)
        assert oee.oee_score == pytest.approx(expected_quality, rel=1e-9)

    def test_calculate_oee_realistic_scenario(self):
        """Should calculate OEE for realistic manufacturing scenario"""
        from app.domain.entities.machine import OEECalculator

        # 8 hour shift = 480 minutes
        # Downtime: 30 minutes (lunch + breakdown) = 93.75% availability
        # Running time: 450 minutes
        # Ideal: 450 pieces, Actual: 400 pieces = 88.89% performance
        # Defects: 20 out of 400 = 95% quality
        # OEE = 0.9375 * 0.8889 * 0.95 = 0.7917 (79.17%)

        total_time_minutes = 480
        downtime_minutes = 30
        ideal_cycle_time = 1.0
        total_pieces = 400
        defect_pieces = 20

        oee = OEECalculator.calculate_oee(
            total_time_minutes=total_time_minutes,
            downtime_minutes=downtime_minutes,
            ideal_cycle_time=ideal_cycle_time,
            total_pieces=total_pieces,
            defect_pieces=defect_pieces
        )

        expected_availability = 450 / 480  # 0.9375
        expected_performance = 400 / 450  # 0.8889
        expected_quality = 380 / 400  # 0.95
        expected_oee = expected_availability * expected_performance * expected_quality

        assert oee.availability == pytest.approx(expected_availability, rel=1e-4)
        assert oee.performance == pytest.approx(expected_performance, rel=1e-4)
        assert oee.quality == pytest.approx(expected_quality, rel=1e-4)
        assert oee.oee_score == pytest.approx(expected_oee, rel=1e-4)

    def test_oee_zero_total_time_raises_error(self):
        """Should raise error when total time is zero"""
        from app.domain.entities.machine import OEECalculator

        with pytest.raises(ValueError, match="Total time must be positive"):
            OEECalculator.calculate_oee(
                total_time_minutes=0,
                downtime_minutes=0,
                ideal_cycle_time=1.0,
                total_pieces=100,
                defect_pieces=0
            )

    def test_oee_downtime_exceeds_total_time_raises_error(self):
        """Should raise error when downtime exceeds total time"""
        from app.domain.entities.machine import OEECalculator

        with pytest.raises(ValueError, match="Downtime cannot exceed total time"):
            OEECalculator.calculate_oee(
                total_time_minutes=100,
                downtime_minutes=101,
                ideal_cycle_time=1.0,
                total_pieces=50,
                defect_pieces=0
            )

    def test_oee_negative_values_raise_errors(self):
        """Should raise errors for negative values"""
        from app.domain.entities.machine import OEECalculator

        with pytest.raises(ValueError, match="cannot be negative"):
            OEECalculator.calculate_oee(
                total_time_minutes=480,
                downtime_minutes=-10,
                ideal_cycle_time=1.0,
                total_pieces=400,
                defect_pieces=0
            )


class TestMachineStatusHistory:
    """Test MachineStatusHistory domain entity"""

    def test_create_status_history_entry(self):
        """Should create status history entry"""
        from app.domain.entities.machine import MachineStatusHistoryDomain, MachineStatus

        start_time = datetime(2025, 11, 8, 8, 0, 0)

        history = MachineStatusHistoryDomain(
            id=None,
            machine_id=1,
            status=MachineStatus.RUNNING,
            started_at=start_time,
            ended_at=None,
            notes="Started production shift"
        )

        assert history.machine_id == 1
        assert history.status == MachineStatus.RUNNING
        assert history.started_at == start_time
        assert history.ended_at is None

    def test_calculate_status_duration(self):
        """Should calculate duration between start and end time"""
        from app.domain.entities.machine import MachineStatusHistoryDomain, MachineStatus

        start_time = datetime(2025, 11, 8, 8, 0, 0)
        end_time = datetime(2025, 11, 8, 10, 30, 0)

        history = MachineStatusHistoryDomain(
            id=1,
            machine_id=1,
            status=MachineStatus.RUNNING,
            started_at=start_time,
            ended_at=end_time
        )

        duration = history.get_duration_minutes()
        assert duration == 150  # 2.5 hours = 150 minutes

    def test_ongoing_status_returns_none_duration(self):
        """Should return None for duration if status is ongoing (no end time)"""
        from app.domain.entities.machine import MachineStatusHistoryDomain, MachineStatus

        history = MachineStatusHistoryDomain(
            id=1,
            machine_id=1,
            status=MachineStatus.RUNNING,
            started_at=datetime(2025, 11, 8, 8, 0, 0),
            ended_at=None
        )

        duration = history.get_duration_minutes()
        assert duration is None

    def test_end_status_period(self):
        """Should end status period by setting ended_at"""
        from app.domain.entities.machine import MachineStatusHistoryDomain, MachineStatus

        history = MachineStatusHistoryDomain(
            id=1,
            machine_id=1,
            status=MachineStatus.RUNNING,
            started_at=datetime(2025, 11, 8, 8, 0, 0),
            ended_at=None
        )

        end_time = datetime(2025, 11, 8, 12, 0, 0)
        history.end_period(end_time)

        assert history.ended_at == end_time
        assert history.get_duration_minutes() == 240  # 4 hours
