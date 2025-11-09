"""
SQLAlchemy models for Shift Management domain.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Time, Text, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Shift(Base):
    """
    Shift entity - shift patterns and schedules.

    Represents shift patterns with start/end times and production targets.
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    """
    __tablename__ = "shift"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    shift_name = Column(String(100), nullable=False)
    shift_code = Column(String(20), nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    production_target = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    from_handovers = relationship("ShiftHandover", foreign_keys="ShiftHandover.from_shift_id", back_populates="from_shift")
    to_handovers = relationship("ShiftHandover", foreign_keys="ShiftHandover.to_shift_id", back_populates="to_shift")

    # Unique constraint: shift_code per organization and plant
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id', 'shift_code',
                         name='uq_shift_code_per_plant'),
        Index('idx_shift_org_plant', 'organization_id', 'plant_id'),
        Index('idx_shift_active', 'is_active'),
        CheckConstraint('production_target >= 0', name='check_production_target_non_negative'),
    )

    def __repr__(self):
        return f"<Shift(code='{self.shift_code}', name='{self.shift_name}', org={self.organization_id})>"


class ShiftHandover(Base):
    """
    Shift Handover entity - handover notes between shifts.

    Represents shift handovers with WIP status, production summary, and issues.
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    """
    __tablename__ = "shift_handover"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    from_shift_id = Column(Integer, ForeignKey('shift.id', ondelete='CASCADE'), nullable=False, index=True)
    to_shift_id = Column(Integer, ForeignKey('shift.id', ondelete='CASCADE'), nullable=False, index=True)
    handover_date = Column(DateTime(timezone=True), nullable=False, index=True)
    wip_quantity = Column(Float, nullable=False, default=0.0)
    production_summary = Column(Text, nullable=False)
    quality_issues = Column(Text, nullable=True)
    machine_status = Column(Text, nullable=True)
    material_status = Column(Text, nullable=True)
    safety_incidents = Column(Text, nullable=True)
    handover_by_user_id = Column(Integer, nullable=False)
    acknowledged_by_user_id = Column(Integer, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    from_shift = relationship("Shift", foreign_keys=[from_shift_id], back_populates="from_handovers")
    to_shift = relationship("Shift", foreign_keys=[to_shift_id], back_populates="to_handovers")

    # Constraints
    __table_args__ = (
        Index('idx_shift_handover_org_plant', 'organization_id', 'plant_id'),
        Index('idx_shift_handover_date', 'handover_date'),
        Index('idx_shift_handover_from_shift', 'from_shift_id'),
        Index('idx_shift_handover_to_shift', 'to_shift_id'),
        CheckConstraint('wip_quantity >= 0', name='check_wip_quantity_non_negative'),
        CheckConstraint('from_shift_id != to_shift_id', name='check_different_shifts'),
    )

    def __repr__(self):
        return f"<ShiftHandover(from={self.from_shift_id}, to={self.to_shift_id}, date={self.handover_date})>"


class ShiftPerformance(Base):
    """
    Shift Performance entity - performance metrics per shift.

    Stores calculated performance metrics like target attainment, OEE, FPY.
    Can be calculated on-demand or via pg_cron for historical tracking.
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    """
    __tablename__ = "shift_performance"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    shift_id = Column(Integer, ForeignKey('shift.id', ondelete='CASCADE'), nullable=False, index=True)
    performance_date = Column(DateTime(timezone=True), nullable=False, index=True)

    # Production metrics
    production_target = Column(Float, nullable=False)
    production_actual = Column(Float, nullable=False, default=0.0)
    target_attainment_percent = Column(Float, nullable=False, default=0.0)

    # OEE metrics (Overall Equipment Effectiveness)
    availability_percent = Column(Float, nullable=True)
    performance_percent = Column(Float, nullable=True)
    quality_percent = Column(Float, nullable=True)
    oee_percent = Column(Float, nullable=True)

    # Quality metrics
    total_produced = Column(Float, nullable=False, default=0.0)
    total_good = Column(Float, nullable=False, default=0.0)
    total_rejected = Column(Float, nullable=False, default=0.0)
    fpy_percent = Column(Float, nullable=True)  # First Pass Yield

    # Time metrics (minutes)
    planned_production_time = Column(Float, nullable=True)
    actual_run_time = Column(Float, nullable=True)
    downtime_minutes = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shift = relationship("Shift")

    # Unique constraint: one performance record per shift per date
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id', 'shift_id', 'performance_date',
                         name='uq_shift_performance_per_date'),
        Index('idx_shift_performance_org_plant', 'organization_id', 'plant_id'),
        Index('idx_shift_performance_date', 'performance_date'),
        CheckConstraint('production_target >= 0', name='check_perf_target_non_negative'),
        CheckConstraint('production_actual >= 0', name='check_perf_actual_non_negative'),
        CheckConstraint('target_attainment_percent >= 0', name='check_target_attainment_non_negative'),
        CheckConstraint('total_produced >= 0', name='check_total_produced_non_negative'),
        CheckConstraint('total_good >= 0', name='check_total_good_non_negative'),
        CheckConstraint('total_rejected >= 0', name='check_total_rejected_non_negative'),
    )

    def __repr__(self):
        return f"<ShiftPerformance(shift={self.shift_id}, date={self.performance_date}, attainment={self.target_attainment_percent}%)>"
