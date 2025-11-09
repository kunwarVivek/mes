"""
SQLAlchemy models for Machine & Equipment domain.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Index, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.domain.entities.machine import MachineStatus


class Machine(Base):
    """
    Machine entity - represents production equipment and machinery.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Tracks machine status and links to work centers.
    """
    __tablename__ = "machine"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    machine_code = Column(String(20), unique=True, nullable=False, index=True)
    machine_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    work_center_id = Column(Integer, nullable=False, index=True)
    status = Column(Enum(MachineStatus), nullable=False, default=MachineStatus.AVAILABLE)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    status_history = relationship(
        "MachineStatusHistory",
        back_populates="machine",
        cascade="all, delete-orphan",
        order_by="desc(MachineStatusHistory.started_at)"
    )

    # Indexes for RLS and common queries
    __table_args__ = (
        Index('idx_machine_org_plant', 'organization_id', 'plant_id'),
        Index('idx_machine_work_center', 'work_center_id'),
        Index('idx_machine_status', 'status'),
    )

    def __repr__(self):
        return f"<Machine(code='{self.machine_code}', status='{self.status}', org={self.organization_id})>"


class MachineStatusHistory(Base):
    """
    Machine Status History - tracks status changes over time using TimescaleDB hypertable.

    This table should be converted to a TimescaleDB hypertable for efficient time-series queries.
    Enables OEE calculation by tracking machine availability periods.
    """
    __tablename__ = "machine_status_history"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey('machine.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(Enum(MachineStatus), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    machine = relationship("Machine", back_populates="status_history")

    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_machine_status_history_machine_time', 'machine_id', 'started_at'),
        Index('idx_machine_status_history_time_range', 'started_at', 'ended_at'),
    )

    def __repr__(self):
        duration = (self.ended_at - self.started_at).total_seconds() / 60.0 if self.ended_at else None
        return f"<MachineStatusHistory(machine_id={self.machine_id}, status='{self.status}', duration={duration}min)>"
