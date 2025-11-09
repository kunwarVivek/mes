"""
Unit tests for Maintenance domain entities.

Test Coverage:
- PMScheduleDomain: Schedule validation, trigger type validation
- PMWorkOrderDomain: Auto-generation logic, status transitions
- DowntimeEventDomain: Category validation, duration calculation
- MTBFMTTRCalculator: MTBF and MTTR calculations
"""

import pytest
from datetime import datetime, timedelta


class TestPMScheduleDomain:
    """Test PM Schedule domain entity business logic"""

    def test_create_calendar_based_pm_schedule(self):
        """Should create calendar-based PM schedule with valid data"""
        from app.domain.entities.maintenance import PMScheduleDomain, TriggerType

        schedule = PMScheduleDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            schedule_code="PM-001",
            schedule_name="Monthly PM Check",
            machine_id=1,
            trigger_type=TriggerType.CALENDAR,
            frequency_days=30,
            meter_threshold=None,
            is_active=True
        )

        assert schedule.schedule_code == "PM-001"
        assert schedule.trigger_type == TriggerType.CALENDAR
        assert schedule.frequency_days == 30
        assert schedule.is_active is True

    def test_create_meter_based_pm_schedule(self):
        """Should create meter-based PM schedule with valid data"""
        from app.domain.entities.maintenance import PMScheduleDomain, TriggerType

        schedule = PMScheduleDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            schedule_code="PM-002",
            schedule_name="Every 1000 Hours PM",
            machine_id=1,
            trigger_type=TriggerType.METER,
            frequency_days=None,
            meter_threshold=1000.0,
            is_active=True
        )

        assert schedule.trigger_type == TriggerType.METER
        assert schedule.meter_threshold == 1000.0

    def test_calendar_schedule_requires_frequency_days(self):
        """Should require frequency_days for calendar-based schedules"""
        from app.domain.entities.maintenance import PMScheduleDomain, TriggerType

        with pytest.raises(ValueError, match="Calendar-based schedules require frequency_days"):
            PMScheduleDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                schedule_code="PM-001",
                schedule_name="Monthly PM",
                machine_id=1,
                trigger_type=TriggerType.CALENDAR,
                frequency_days=None,  # Missing required field
                meter_threshold=None
            )

    def test_meter_schedule_requires_meter_threshold(self):
        """Should require meter_threshold for meter-based schedules"""
        from app.domain.entities.maintenance import PMScheduleDomain, TriggerType

        with pytest.raises(ValueError, match="Meter-based schedules require meter_threshold"):
            PMScheduleDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                schedule_code="PM-002",
                schedule_name="Hour-based PM",
                machine_id=1,
                trigger_type=TriggerType.METER,
                frequency_days=None,
                meter_threshold=None  # Missing required field
            )

    def test_schedule_code_cannot_be_empty(self):
        """Should validate schedule code is not empty"""
        from app.domain.entities.maintenance import PMScheduleDomain, TriggerType

        with pytest.raises(ValueError, match="Schedule code cannot be empty"):
            PMScheduleDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                schedule_code="",  # Invalid
                schedule_name="PM Schedule",
                machine_id=1,
                trigger_type=TriggerType.CALENDAR,
                frequency_days=30,
                meter_threshold=None
            )

    def test_frequency_days_must_be_positive(self):
        """Should validate frequency_days is positive when provided"""
        from app.domain.entities.maintenance import PMScheduleDomain, TriggerType

        with pytest.raises(ValueError, match="Frequency days must be positive"):
            PMScheduleDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                schedule_code="PM-001",
                schedule_name="PM Schedule",
                machine_id=1,
                trigger_type=TriggerType.CALENDAR,
                frequency_days=-5,  # Invalid
                meter_threshold=None
            )

    def test_activate_deactivate_schedule(self):
        """Should activate and deactivate PM schedule"""
        from app.domain.entities.maintenance import PMScheduleDomain, TriggerType

        schedule = PMScheduleDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            schedule_code="PM-001",
            schedule_name="Monthly PM",
            machine_id=1,
            trigger_type=TriggerType.CALENDAR,
            frequency_days=30,
            meter_threshold=None,
            is_active=True
        )

        schedule.deactivate()
        assert schedule.is_active is False

        schedule.activate()
        assert schedule.is_active is True


class TestPMWorkOrderDomain:
    """Test PM Work Order domain entity business logic"""

    def test_create_pm_work_order(self):
        """Should create PM work order with valid data"""
        from app.domain.entities.maintenance import PMWorkOrderDomain, PMStatus

        work_order = PMWorkOrderDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            pm_schedule_id=1,
            machine_id=1,
            pm_number="PMWO-001",
            status=PMStatus.SCHEDULED,
            scheduled_date=datetime(2025, 11, 15),
            due_date=datetime(2025, 11, 15)
        )

        assert work_order.pm_number == "PMWO-001"
        assert work_order.status == PMStatus.SCHEDULED
        assert work_order.scheduled_date == datetime(2025, 11, 15)

    def test_pm_work_order_status_transitions(self):
        """Should transition PM work order through valid statuses"""
        from app.domain.entities.maintenance import PMWorkOrderDomain, PMStatus

        work_order = PMWorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            pm_schedule_id=1,
            machine_id=1,
            pm_number="PMWO-001",
            status=PMStatus.SCHEDULED,
            scheduled_date=datetime.utcnow(),
            due_date=datetime.utcnow()
        )

        # SCHEDULED -> IN_PROGRESS
        work_order.start()
        assert work_order.status == PMStatus.IN_PROGRESS
        assert work_order.started_at is not None

        # IN_PROGRESS -> COMPLETED
        work_order.complete()
        assert work_order.status == PMStatus.COMPLETED
        assert work_order.completed_at is not None

    def test_pm_work_order_can_only_start_from_scheduled(self):
        """Should only allow starting PM work order from SCHEDULED status"""
        from app.domain.entities.maintenance import PMWorkOrderDomain, PMStatus

        work_order = PMWorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            pm_schedule_id=1,
            machine_id=1,
            pm_number="PMWO-001",
            status=PMStatus.COMPLETED,  # Already completed
            scheduled_date=datetime.utcnow(),
            due_date=datetime.utcnow()
        )

        with pytest.raises(ValueError, match="can only be started from SCHEDULED status"):
            work_order.start()

    def test_pm_number_cannot_be_empty(self):
        """Should validate PM number is not empty"""
        from app.domain.entities.maintenance import PMWorkOrderDomain, PMStatus

        with pytest.raises(ValueError, match="PM number cannot be empty"):
            PMWorkOrderDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                pm_schedule_id=1,
                machine_id=1,
                pm_number="",  # Invalid
                status=PMStatus.SCHEDULED,
                scheduled_date=datetime.utcnow(),
                due_date=datetime.utcnow()
            )


class TestDowntimeEventDomain:
    """Test Downtime Event domain entity business logic"""

    def test_create_downtime_event(self):
        """Should create downtime event with valid data"""
        from app.domain.entities.maintenance import DowntimeEventDomain, DowntimeCategory

        event = DowntimeEventDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            machine_id=1,
            category=DowntimeCategory.BREAKDOWN,
            reason="Motor failure",
            started_at=datetime(2025, 11, 8, 10, 0),
            ended_at=None
        )

        assert event.category == DowntimeCategory.BREAKDOWN
        assert event.reason == "Motor failure"
        assert event.ended_at is None

    def test_downtime_event_duration_calculation(self):
        """Should calculate downtime duration in minutes"""
        from app.domain.entities.maintenance import DowntimeEventDomain, DowntimeCategory

        started = datetime(2025, 11, 8, 10, 0)
        ended = datetime(2025, 11, 8, 12, 30)

        event = DowntimeEventDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            machine_id=1,
            category=DowntimeCategory.BREAKDOWN,
            reason="Motor failure",
            started_at=started,
            ended_at=ended
        )

        duration = event.get_duration_minutes()
        assert duration == 150.0  # 2.5 hours = 150 minutes

    def test_ongoing_downtime_returns_none_duration(self):
        """Should return None for ongoing downtime events"""
        from app.domain.entities.maintenance import DowntimeEventDomain, DowntimeCategory

        event = DowntimeEventDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            machine_id=1,
            category=DowntimeCategory.BREAKDOWN,
            reason="Motor failure",
            started_at=datetime.utcnow(),
            ended_at=None  # Ongoing
        )

        assert event.get_duration_minutes() is None

    def test_end_downtime_event(self):
        """Should end downtime event with valid end time"""
        from app.domain.entities.maintenance import DowntimeEventDomain, DowntimeCategory

        event = DowntimeEventDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            machine_id=1,
            category=DowntimeCategory.BREAKDOWN,
            reason="Motor failure",
            started_at=datetime(2025, 11, 8, 10, 0),
            ended_at=None
        )

        event.end_event(datetime(2025, 11, 8, 12, 0))
        assert event.ended_at == datetime(2025, 11, 8, 12, 0)
        assert event.get_duration_minutes() == 120.0

    def test_end_time_cannot_be_before_start_time(self):
        """Should validate end time is after start time"""
        from app.domain.entities.maintenance import DowntimeEventDomain, DowntimeCategory

        event = DowntimeEventDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            machine_id=1,
            category=DowntimeCategory.BREAKDOWN,
            reason="Motor failure",
            started_at=datetime(2025, 11, 8, 10, 0),
            ended_at=None
        )

        with pytest.raises(ValueError, match="End time cannot be before start time"):
            event.end_event(datetime(2025, 11, 8, 9, 0))  # Before start

    def test_downtime_category_validation(self):
        """Should validate downtime category is valid enum"""
        from app.domain.entities.maintenance import DowntimeEventDomain, DowntimeCategory

        # Valid categories: BREAKDOWN, PLANNED_MAINTENANCE, CHANGEOVER, NO_OPERATOR, MATERIAL_SHORTAGE
        event = DowntimeEventDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            machine_id=1,
            category=DowntimeCategory.PLANNED_MAINTENANCE,
            reason="Scheduled PM",
            started_at=datetime.utcnow(),
            ended_at=None
        )

        assert event.category == DowntimeCategory.PLANNED_MAINTENANCE


class TestMTBFMTTRCalculator:
    """Test MTBF/MTTR calculation service"""

    def test_calculate_mtbf(self):
        """Should calculate Mean Time Between Failures (MTBF)"""
        from app.domain.entities.maintenance import MTBFMTTRCalculator

        total_operating_time = 10000.0  # minutes
        number_of_failures = 5

        mtbf = MTBFMTTRCalculator.calculate_mtbf(
            total_operating_time=total_operating_time,
            number_of_failures=number_of_failures
        )

        assert mtbf == 2000.0  # 10000 / 5 = 2000 minutes

    def test_calculate_mttr(self):
        """Should calculate Mean Time To Repair (MTTR)"""
        from app.domain.entities.maintenance import MTBFMTTRCalculator

        total_repair_time = 600.0  # minutes
        number_of_failures = 5

        mttr = MTBFMTTRCalculator.calculate_mttr(
            total_repair_time=total_repair_time,
            number_of_failures=number_of_failures
        )

        assert mttr == 120.0  # 600 / 5 = 120 minutes

    def test_calculate_mtbf_mttr_metrics(self):
        """Should calculate complete MTBF/MTTR metrics"""
        from app.domain.entities.maintenance import MTBFMTTRCalculator

        metrics = MTBFMTTRCalculator.calculate_metrics(
            total_operating_time=10000.0,
            total_repair_time=600.0,
            number_of_failures=5
        )

        assert metrics.mtbf == 2000.0
        assert metrics.mttr == 120.0
        assert metrics.availability == pytest.approx(0.943396, rel=1e-5)  # MTBF / (MTBF + MTTR)

    def test_mtbf_requires_positive_operating_time(self):
        """Should validate total operating time is positive"""
        from app.domain.entities.maintenance import MTBFMTTRCalculator

        with pytest.raises(ValueError, match="Total operating time must be positive"):
            MTBFMTTRCalculator.calculate_mtbf(
                total_operating_time=0,  # Invalid
                number_of_failures=5
            )

    def test_mtbf_requires_non_negative_failures(self):
        """Should validate number of failures is non-negative"""
        from app.domain.entities.maintenance import MTBFMTTRCalculator

        with pytest.raises(ValueError, match="Number of failures cannot be negative"):
            MTBFMTTRCalculator.calculate_mtbf(
                total_operating_time=10000.0,
                number_of_failures=-1  # Invalid
            )

    def test_mttr_requires_non_negative_repair_time(self):
        """Should validate total repair time is non-negative"""
        from app.domain.entities.maintenance import MTBFMTTRCalculator

        with pytest.raises(ValueError, match="Total repair time cannot be negative"):
            MTBFMTTRCalculator.calculate_mttr(
                total_repair_time=-100,  # Invalid
                number_of_failures=5
            )

    def test_zero_failures_returns_infinite_mtbf(self):
        """Should handle zero failures case (no breakdowns)"""
        from app.domain.entities.maintenance import MTBFMTTRCalculator

        # When there are no failures, MTBF is infinite (perfect reliability)
        # We'll return a special value or handle this edge case
        metrics = MTBFMTTRCalculator.calculate_metrics(
            total_operating_time=10000.0,
            total_repair_time=0.0,
            number_of_failures=0
        )

        assert metrics.mtbf == float('inf')
        assert metrics.mttr == 0.0
        assert metrics.availability == 1.0  # Perfect availability
