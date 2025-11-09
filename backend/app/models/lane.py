"""
SQLAlchemy models for Lane and Lane Assignment
"""
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime, Date,
    ForeignKey, Text, CheckConstraint, UniqueConstraint, Index,
    Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.domain.entities.lane import LaneAssignmentStatus


class Lane(Base):
    """Lane model - Physical production line/area"""
    __tablename__ = "lanes"

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'), nullable=False, index=True)
    lane_code = Column(String(50), nullable=False)
    lane_name = Column(String(200), nullable=False)
    capacity_per_day = Column(Numeric(15, 3), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plant = relationship("Plant", back_populates="lanes")
    assignments = relationship("LaneAssignment", back_populates="lane", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('plant_id', 'lane_code', name='uq_lane_code_per_plant'),
        CheckConstraint('capacity_per_day > 0', name='check_capacity'),
        Index('idx_lane_plant', 'plant_id'),
        Index('idx_lane_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Lane(code='{self.lane_code}', name='{self.lane_name}', capacity={self.capacity_per_day})>"


class LaneAssignment(Base):
    """Lane Assignment model - Scheduled work on lanes"""
    __tablename__ = "lane_assignments"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'), nullable=False, index=True)
    lane_id = Column(Integer, ForeignKey('lanes.id', ondelete='CASCADE'), nullable=False)
    work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='CASCADE'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    scheduled_start = Column(Date, nullable=False)
    scheduled_end = Column(Date, nullable=False)
    allocated_capacity = Column(Numeric(15, 3), nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    status = Column(SQLEnum(LaneAssignmentStatus), default=LaneAssignmentStatus.PLANNED, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    plant = relationship("Plant")
    lane = relationship("Lane", back_populates="assignments")
    work_order = relationship("WorkOrder")
    project = relationship("Project")

    __table_args__ = (
        CheckConstraint('scheduled_end >= scheduled_start', name='check_dates'),
        CheckConstraint('allocated_capacity > 0', name='check_allocated_capacity'),
        Index('idx_lane_assign_org', 'organization_id'),
        Index('idx_lane_assign_plant', 'plant_id'),
        Index('idx_lane_assign_lane_dates', 'lane_id', 'scheduled_start', 'scheduled_end'),
        Index('idx_lane_assign_wo', 'work_order_id'),
        Index('idx_lane_assign_project', 'project_id', postgresql_where=Column('project_id').isnot(None)),
        Index('idx_lane_assign_status', 'status'),
    )

    def __repr__(self):
        return f"<LaneAssignment(lane={self.lane_id}, wo={self.work_order_id}, dates={self.scheduled_start}-{self.scheduled_end})>"
