"""
SQLAlchemy model for Work Center Shift domain.
Work Center Multi-Shift Support - Production Planning Module
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Time, JSON, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.core.database import Base


class WorkCenterShift(Base):
    """
    Work Center Shift entity - shift calendar and scheduling configuration.

    Represents shifts that define when a work center is operational.
    Supports multiple shifts per work center with different capacities and schedules.
    Multi-tenant isolation via work_center relationship (inherits org/plant from WorkCenter).

    Business Rules:
    - Shifts can span across days (e.g., night shift 22:00-06:00)
    - Multiple shifts per work center allowed (e.g., morning, evening, night)
    - Capacity percentage allows modeling of reduced efficiency (e.g., 85% for night shift)
    - Days of week uses ISO standard: 1=Monday, 7=Sunday
    - Overlapping shifts on same days should be validated by business logic
    """
    __tablename__ = "work_center_shift"

    id = Column(Integer, primary_key=True)
    work_center_id = Column(Integer, ForeignKey('work_center.id', ondelete='CASCADE'), nullable=False, index=True)

    # Shift identification
    shift_name = Column(String(50), nullable=False)  # e.g., "Morning", "Evening", "Night", "Weekend"
    shift_number = Column(Integer, nullable=False)   # Numeric identifier: 1, 2, 3

    # Shift timing
    start_time = Column(Time, nullable=False)  # Shift start time (e.g., 06:00)
    end_time = Column(Time, nullable=False)    # Shift end time (e.g., 14:00)

    # Days of operation (ISO 8601: 1=Monday, 7=Sunday)
    days_of_week = Column(JSON, nullable=False)  # e.g., [1,2,3,4,5] for Mon-Fri

    # Capacity and efficiency
    capacity_percentage = Column(Float, nullable=False, default=100.0)  # 100 = normal, 85 = reduced efficiency

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    work_center = relationship("WorkCenter", backref="shifts")

    # Constraints
    __table_args__ = (
        # Unique constraint: shift_number per work_center
        UniqueConstraint('work_center_id', 'shift_number',
                         name='uq_shift_number_per_work_center'),
        # Indexes for query performance
        Index('idx_shift_work_center', 'work_center_id'),
        Index('idx_work_center_shift_active', 'is_active'),
        # Data validation constraints
        CheckConstraint('shift_number > 0', name='check_shift_number_positive'),
        CheckConstraint('capacity_percentage > 0 AND capacity_percentage <= 200',
                        name='check_capacity_percentage_range'),
    )

    def __repr__(self):
        return (f"<WorkCenterShift(wc_id={self.work_center_id}, "
                f"name='{self.shift_name}', number={self.shift_number}, "
                f"time={self.start_time}-{self.end_time})>")

    def get_shift_duration_hours(self) -> float:
        """
        Calculate shift duration in hours.

        Handles shifts that span midnight (e.g., 22:00-06:00).

        Returns:
            Shift duration in hours
        """
        from datetime import datetime, timedelta

        # Create datetime objects for calculation
        base_date = datetime(2000, 1, 1)
        start_dt = datetime.combine(base_date, self.start_time)
        end_dt = datetime.combine(base_date, self.end_time)

        # If end time is before start time, shift spans midnight
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        duration = end_dt - start_dt
        return duration.total_seconds() / 3600.0

    def is_active_on_day(self, day_of_week: int) -> bool:
        """
        Check if shift is active on a specific day of week.

        Args:
            day_of_week: ISO day of week (1=Monday, 7=Sunday)

        Returns:
            True if shift operates on this day
        """
        return day_of_week in self.days_of_week
