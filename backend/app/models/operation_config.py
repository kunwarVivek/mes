"""
SQLAlchemy model for Operation Scheduling Configuration.
Stores default scheduling behavior per organization, plant, and work center.
"""
from sqlalchemy import Column, Integer, Boolean, Float, ForeignKey, Enum, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.core.database import Base
from app.models.work_order import SchedulingMode


class OperationSchedulingConfig(Base):
    """
    Operation Scheduling Configuration entity.

    Defines default scheduling behavior for operations at organization/plant/work center level.
    Supports hierarchical configuration: global (work_center_id=NULL) or work center specific.
    """
    __tablename__ = "operation_scheduling_config"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    work_center_id = Column(Integer, ForeignKey('work_center.id', ondelete='CASCADE'), nullable=True, index=True)

    # Default scheduling settings
    default_scheduling_mode = Column(Enum(SchedulingMode), nullable=False, default=SchedulingMode.SEQUENTIAL)
    default_overlap_percentage = Column(Float, nullable=False, default=0.0)
    allow_parallel_operations = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    work_center = relationship("WorkCenter")

    # Unique constraint: one config per organization/plant/work_center combination
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id', 'work_center_id',
                         name='uq_scheduling_config_per_work_center'),
        Index('idx_scheduling_config_org_plant', 'organization_id', 'plant_id'),
        CheckConstraint('default_overlap_percentage >= 0 AND default_overlap_percentage <= 100',
                        name='check_default_overlap_percentage_range'),
    )

    def __repr__(self):
        return f"<OperationSchedulingConfig(org={self.organization_id}, plant={self.plant_id}, wc={self.work_center_id})>"
