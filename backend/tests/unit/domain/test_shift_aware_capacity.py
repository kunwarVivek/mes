"""
Integration tests for shift-aware capacity calculations.
Work Center Multi-Shift Support - Integration with CapacityCalculator

Tests the integration between CapacityCalculator and ShiftCalendarService.
"""
import pytest
from datetime import datetime, time, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.services.capacity_calculator import CapacityCalculator
from app.models.work_center_shift import WorkCenterShift
from app.models.work_order import WorkCenter, WorkCenterType


class TestShiftAwareCapacity:
    """Test suite for shift-aware capacity calculations"""

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

    def test_capacity_calculator_with_shifts(self, db_session, work_center):
        """Test CapacityCalculator uses shift calendar when enabled"""
        # Create two shifts
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
        evening_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Evening",
            shift_number=2,
            start_time=time(14, 0),
            end_time=time(22, 0),
            days_of_week=[1, 2, 3, 4, 5],  # Mon-Fri
            capacity_percentage=85.0,
            is_active=True
        )
        db_session.add_all([morning_shift, evening_shift])
        db_session.commit()

        # Test with shift calendar enabled
        calculator = CapacityCalculator(db_session, use_shift_calendar=True)

        # Calculate capacity for one week (Mon-Sun)
        start_date = datetime(2025, 11, 10)  # Monday
        end_date = datetime(2025, 11, 16)    # Sunday

        result = calculator.calculate_work_center_load(
            work_center.id,
            start_date,
            end_date
        )

        # Expected: 5 weekdays * (8h morning + 6.8h evening) = 5 * 14.8 = 74 hours
        expected_capacity = 5 * (8.0 + 6.8)
        assert result['capacity_hours'] == pytest.approx(expected_capacity, rel=0.01)

    def test_capacity_calculator_legacy_mode(self, db_session, work_center):
        """Test CapacityCalculator legacy mode ignores shifts"""
        # Create shifts (should be ignored)
        shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Morning",
            shift_number=1,
            start_time=time(6, 0),
            end_time=time(14, 0),
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=100.0,
            is_active=True
        )
        db_session.add(shift)
        db_session.commit()

        # Test with shift calendar disabled (legacy mode)
        calculator = CapacityCalculator(db_session, use_shift_calendar=False)

        start_date = datetime(2025, 11, 10)
        end_date = datetime(2025, 11, 16)

        result = calculator.calculate_work_center_load(
            work_center.id,
            start_date,
            end_date
        )

        # Legacy: 7 days * 8 hours = 56 hours (ignores shifts)
        assert result['capacity_hours'] == 56.0

    def test_capacity_with_no_shifts_configured(self, db_session, work_center):
        """Test that work centers without shifts fall back gracefully"""
        # No shifts configured for this work center
        calculator = CapacityCalculator(db_session, use_shift_calendar=True)

        start_date = datetime(2025, 11, 10)
        end_date = datetime(2025, 11, 16)

        result = calculator.calculate_work_center_load(
            work_center.id,
            start_date,
            end_date
        )

        # With no shifts configured, capacity should be 0
        assert result['capacity_hours'] == 0.0

    def test_capacity_with_weekend_only_shifts(self, db_session, work_center):
        """Test capacity calculation with weekend-only shifts"""
        # Weekend shift only
        weekend_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Weekend",
            shift_number=1,
            start_time=time(8, 0),
            end_time=time(16, 0),
            days_of_week=[6, 7],  # Sat-Sun
            capacity_percentage=100.0,
            is_active=True
        )
        db_session.add(weekend_shift)
        db_session.commit()

        calculator = CapacityCalculator(db_session, use_shift_calendar=True)

        # Week from Monday to Sunday
        start_date = datetime(2025, 11, 10)  # Monday
        end_date = datetime(2025, 11, 16)    # Sunday

        result = calculator.calculate_work_center_load(
            work_center.id,
            start_date,
            end_date
        )

        # Only 2 weekend days * 8 hours = 16 hours
        assert result['capacity_hours'] == 16.0

    def test_capacity_with_reduced_efficiency_night_shift(self, db_session, work_center):
        """Test that reduced capacity percentage is properly applied"""
        # Night shift with 80% efficiency
        night_shift = WorkCenterShift(
            work_center_id=work_center.id,
            shift_name="Night",
            shift_number=1,
            start_time=time(22, 0),
            end_time=time(6, 0),  # Spans midnight
            days_of_week=[1, 2, 3, 4, 5],
            capacity_percentage=80.0,
            is_active=True
        )
        db_session.add(night_shift)
        db_session.commit()

        calculator = CapacityCalculator(db_session, use_shift_calendar=True)

        start_date = datetime(2025, 11, 10)  # Monday
        end_date = datetime(2025, 11, 14)    # Friday (5 days)

        result = calculator.calculate_work_center_load(
            work_center.id,
            start_date,
            end_date
        )

        # 5 weekdays * 8 hours * 80% = 32 effective hours
        expected_capacity = 5 * 8.0 * 0.80
        assert result['capacity_hours'] == pytest.approx(expected_capacity, rel=0.01)
