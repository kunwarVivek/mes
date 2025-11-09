"""
Unit tests for ShiftCalendarService domain service.
Work Center Multi-Shift Support - TDD Implementation

Test Coverage:
- Shift overlap detection
- Capacity calculation across shifts
- Shift transitions and downtime
- Holiday handling
- Multi-shift scheduling
"""
import pytest
from datetime import datetime, time, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.services.shift_calendar_service import ShiftCalendarService
from app.models.work_center_shift import WorkCenterShift
from app.models.work_order import WorkCenter, WorkCenterType


class TestShiftCalendarService:
    """Test suite for ShiftCalendarService domain service - TDD approach"""

    @pytest.fixture
    def db_engine(self):
        """Create in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def db_session(self, db_engine):
        """Create a database session for testing"""
        Session = sessionmaker(bind=db_engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def work_center(self, db_session):
        """Create a test work center"""
        wc = WorkCenter(
            id=1,
            organization_id=1,
            plant_id=1,
            work_center_code="WC001",
            work_center_name="Assembly Line 1",
            work_center_type=WorkCenterType.ASSEMBLY,
            capacity_per_hour=100.0,
            cost_per_hour=50.0,
            is_active=True
        )
        db_session.add(wc)
        db_session.commit()
        return wc

    @pytest.fixture
    def shift_calendar_service(self, db_session):
        """Create ShiftCalendarService instance"""
        return ShiftCalendarService(db_session)

    # RED Test 1: Shift overlap detection
    def test_detect_shift_time_overlap(self, shift_calendar_service, work_center, db_session):
        """Test detection of overlapping shift times"""
        # Create morning shift: 06:00-14:00
        morning_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Morning",
            shift_number=1,
            start_time=time(6, 0),
            end_time=time(14, 0),
            days_of_week=[1, 2, 3, 4, 5],  # Mon-Fri
            capacity_percentage=100.0,
            is_active=True
        )
        db_session.add(morning_shift)
        db_session.commit()

        # Attempt to create overlapping shift: 12:00-20:00 (overlaps 12:00-14:00)
        overlapping_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Evening",
            shift_number=2,
            start_time=time(12, 0),
            end_time=time(20, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=True
        )

        # Should detect overlap
        has_overlap = shift_calendar_service.detect_shift_overlap(
            work_center.id,
            overlapping_shift.start_time,
            overlapping_shift.end_time,
            overlapping_shift.days_of_week
        )
        assert has_overlap is True

    # RED Test 2: No overlap for non-overlapping shifts
    def test_no_overlap_for_sequential_shifts(self, shift_calendar_service, work_center, db_session):
        """Test that sequential non-overlapping shifts are allowed"""
        # Morning shift: 06:00-14:00
        morning_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Morning",
            shift_number=1,
            start_time=time(6, 0),
            end_time=time(14, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=True
        )
        db_session.add(morning_shift)
        db_session.commit()

        # Evening shift: 14:00-22:00 (no overlap)
        evening_shift_time = (time(14, 0), time(22, 0))

        has_overlap = shift_calendar_service.detect_shift_overlap(
            work_center.id,
            evening_shift_time[0],
            evening_shift_time[1],
            [1, 2, 3, 4, 5]
        )
        assert has_overlap is False

    # RED Test 3: Calculate capacity across multiple shifts
    def test_calculate_daily_capacity_multiple_shifts(self, shift_calendar_service, work_center, db_session):
        """Test capacity calculation with multiple shifts per day"""
        # Morning shift: 06:00-14:00 (8 hours, 100% capacity)
        morning_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Morning",
            shift_number=1,
            start_time=time(6, 0),
            end_time=time(14, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=True
        )

        # Evening shift: 14:00-22:00 (8 hours, 85% capacity - reduced efficiency)
        evening_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Evening",
            shift_number=2,
            start_time=time(14, 0),
            end_time=time(22, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=85.0,
            is_active=True
        )

        db_session.add_all([morning_shift, evening_shift])
        db_session.commit()

        # Calculate capacity for Monday (day_of_week=1)
        test_date = datetime(2025, 11, 10)  # Monday
        capacity_hours = shift_calendar_service.calculate_daily_capacity(
            work_center.id,
            test_date
        )

        # Morning: 8 hours * 100% = 8.0 hours
        # Evening: 8 hours * 85% = 6.8 hours
        # Total: 14.8 effective hours
        expected_capacity = 8.0 + 6.8
        assert capacity_hours == pytest.approx(expected_capacity, rel=0.01)

    # RED Test 4: Weekend shifts (different days_of_week)
    def test_calculate_capacity_weekend_vs_weekday(self, shift_calendar_service, work_center, db_session):
        """Test capacity calculation respects days_of_week configuration"""
        # Weekday shift: Mon-Fri only
        weekday_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Weekday",
            shift_number=1,
            start_time=time(8, 0),
            end_time=time(16, 0),
            days_of_week=[1, 2, 3, 4, 5],  # Mon-Fri
            capacity_percentage=100.0,
            is_active=True
        )

        # Weekend shift: Sat-Sun only
        weekend_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Weekend",
            shift_number=2,
            start_time=time(8, 0),
            end_time=time(16, 0),
            days_of_week=[6, 7],  # Sat-Sun
            capacity_percentage=100.0,
            is_active=True
        )

        db_session.add_all([weekday_shift, weekend_shift])
        db_session.commit()

        # Test Monday (should only count weekday shift)
        monday = datetime(2025, 11, 10)
        monday_capacity = shift_calendar_service.calculate_daily_capacity(work_center.id, monday)
        assert monday_capacity == 8.0

        # Test Saturday (should only count weekend shift)
        saturday = datetime(2025, 11, 15)
        saturday_capacity = shift_calendar_service.calculate_daily_capacity(work_center.id, saturday)
        assert saturday_capacity == 8.0

    # RED Test 5: Inactive shifts should not contribute to capacity
    def test_inactive_shifts_excluded_from_capacity(self, shift_calendar_service, work_center, db_session):
        """Test that inactive shifts are excluded from capacity calculations"""
        # Active shift
        active_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Morning",
            shift_number=1,
            start_time=time(6, 0),
            end_time=time(14, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=True
        )

        # Inactive shift
        inactive_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Night",
            shift_number=3,
            start_time=time(22, 0),
            end_time=time(6, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=False
        )

        db_session.add_all([active_shift, inactive_shift])
        db_session.commit()

        test_date = datetime(2025, 11, 10)
        capacity_hours = shift_calendar_service.calculate_daily_capacity(work_center.id, test_date)

        # Should only count active shift (8 hours)
        assert capacity_hours == 8.0

    # RED Test 6: Shift spanning midnight (night shift)
    def test_night_shift_spanning_midnight(self, shift_calendar_service, work_center, db_session):
        """Test handling of shifts that span midnight"""
        # Night shift: 22:00-06:00 (spans midnight)
        night_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Night",
            shift_number=3,
            start_time=time(22, 0),
            end_time=time(6, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=90.0,
            is_active=True
        )

        db_session.add(night_shift)
        db_session.commit()

        test_date = datetime(2025, 11, 10)
        capacity_hours = shift_calendar_service.calculate_daily_capacity(work_center.id, test_date)

        # Night shift: 8 hours * 90% = 7.2 hours
        assert capacity_hours == pytest.approx(7.2, rel=0.01)

    # RED Test 7: Get active shifts for specific date
    def test_get_active_shifts_for_date(self, shift_calendar_service, work_center, db_session):
        """Test retrieving active shifts for a specific date"""
        shifts = [
            WorkCenterShift(
                work_center_id=work_center.id,
                shift_name="Morning",
                shift_number=1,
                start_time=time(6, 0),
                end_time=time(14, 0),
                days_of_week=[1, 2, 3, 4, 5],
                capacity_percentage=100.0,
                is_active=True
            ),
            WorkCenterShift(
                work_center_id=work_center.id,
                shift_name="Weekend",
                shift_number=2,
                start_time=time(8, 0),
                end_time=time(16, 0),
                days_of_week=[6, 7],
                capacity_percentage=100.0,
                is_active=True
            )
        ]
        db_session.add_all(shifts)
        db_session.commit()

        # Monday should return only Morning shift
        monday = datetime(2025, 11, 10)
        active_shifts = shift_calendar_service.get_active_shifts_for_date(work_center.id, monday)
        assert len(active_shifts) == 1
        assert active_shifts[0].shift_name == "Morning"

        # Saturday should return only Weekend shift
        saturday = datetime(2025, 11, 15)
        active_shifts = shift_calendar_service.get_active_shifts_for_date(work_center.id, saturday)
        assert len(active_shifts) == 1
        assert active_shifts[0].shift_name == "Weekend"

    # RED Test 8: Calculate capacity for date range
    def test_calculate_period_capacity(self, shift_calendar_service, work_center, db_session):
        """Test capacity calculation over a date range"""
        # Single shift: 8 hours/day, Mon-Fri
        shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Standard",
            shift_number=1,
            start_time=time(8, 0),
            end_time=time(16, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=True
        )
        db_session.add(shift)
        db_session.commit()

        # Week from Monday to Sunday (5 working days)
        start_date = datetime(2025, 11, 10)  # Monday
        end_date = datetime(2025, 11, 16)    # Sunday

        total_capacity = shift_calendar_service.calculate_period_capacity(
            work_center.id,
            start_date,
            end_date
        )

        # 5 weekdays * 8 hours = 40 hours
        assert total_capacity == 40.0

    # RED Test 9: Shift transition downtime
    def test_shift_transition_downtime(self, shift_calendar_service, work_center, db_session):
        """Test handling of downtime during shift transitions"""
        # Morning shift: 06:00-14:00
        morning_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Morning",
            shift_number=1,
            start_time=time(6, 0),
            end_time=time(14, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=True
        )

        # Evening shift: 14:30-22:30 (30 min transition/cleanup time)
        evening_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Evening",
            shift_number=2,
            start_time=time(14, 30),
            end_time=time(22, 30),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=True
        )

        db_session.add_all([morning_shift, evening_shift])
        db_session.commit()

        # Calculate total effective hours (should account for gap)
        test_date = datetime(2025, 11, 10)
        capacity_hours = shift_calendar_service.calculate_daily_capacity(work_center.id, test_date)

        # Morning: 8 hours, Evening: 8 hours, Total: 16 hours (gap doesn't reduce capacity)
        assert capacity_hours == 16.0

    # RED Test 10: Overtime shift support
    def test_overtime_shift_capacity(self, shift_calendar_service, work_center, db_session):
        """Test overtime shifts with premium capacity factors"""
        # Regular shift
        regular_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Regular",
            shift_number=1,
            start_time=time(8, 0),
            end_time=time(16, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=True
        )

        # Overtime shift on Saturday (100% capacity despite being overtime)
        overtime_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Overtime",
            shift_number=2,
            start_time=time(8, 0),
            end_time=time(12, 0),  # 4 hours
            days_of_week=[6],  # Saturday only
            capacity_percentage=100.0,
            is_active=True
        )

        db_session.add_all([regular_shift, overtime_shift])
        db_session.commit()

        # Saturday capacity (overtime only)
        saturday = datetime(2025, 11, 15)
        capacity = shift_calendar_service.calculate_daily_capacity(work_center.id, saturday)
        assert capacity == 4.0
