"""
SQLAlchemy models for Quality Management - Inspection domain.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, Index, CheckConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class InspectionFrequency(str, enum.Enum):
    """Enum for inspection frequency"""
    PER_LOT = "PER_LOT"
    PER_SHIFT = "PER_SHIFT"
    HOURLY = "HOURLY"
    CONTINUOUS = "CONTINUOUS"


class InspectionPlan(Base):
    """
    Inspection Plan entity.

    Defines inspection criteria and characteristics for materials.
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Links to Material entity.
    """
    __tablename__ = "inspection_plan"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    plan_name = Column(String(100), nullable=False)
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    inspection_frequency = Column(Enum(InspectionFrequency), nullable=False)
    sample_size = Column(Integer, nullable=False)
    characteristics = Column(JSON, nullable=True)  # Array of inspection characteristics
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    material = relationship("Material", backref="inspection_plans")
    inspection_logs = relationship("InspectionLog", back_populates="inspection_plan", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        Index('idx_inspection_plan_org_plant', 'organization_id', 'plant_id'),
        Index('idx_inspection_plan_material', 'material_id'),
        CheckConstraint('sample_size > 0', name='check_inspection_sample_size_positive'),
    )

    def __repr__(self):
        return f"<InspectionPlan(name='{self.plan_name}', material_id={self.material_id})>"


class InspectionLog(Base):
    """
    Inspection Log entity.

    Records results of inspections performed on work orders.
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Links to InspectionPlan and WorkOrder entities.
    """
    __tablename__ = "inspection_log"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    inspection_plan_id = Column(Integer, ForeignKey('inspection_plan.id', ondelete='CASCADE'), nullable=False, index=True)
    work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='CASCADE'), nullable=False, index=True)
    inspected_quantity = Column(Integer, nullable=False)
    passed_quantity = Column(Integer, nullable=False)
    failed_quantity = Column(Integer, nullable=False)
    inspector_user_id = Column(Integer, nullable=False)
    inspection_notes = Column(String(500), nullable=True)
    measurement_data = Column(JSON, nullable=True)  # Actual measurements for SPC
    inspected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    inspection_plan = relationship("InspectionPlan", back_populates="inspection_logs")
    work_order = relationship("WorkOrder", backref="inspection_logs")

    # Constraints
    __table_args__ = (
        Index('idx_inspection_log_org_plant', 'organization_id', 'plant_id'),
        Index('idx_inspection_log_plan', 'inspection_plan_id'),
        Index('idx_inspection_log_work_order', 'work_order_id'),
        CheckConstraint('inspected_quantity > 0', name='check_inspection_inspected_positive'),
        CheckConstraint('passed_quantity >= 0', name='check_inspection_passed_non_negative'),
        CheckConstraint('failed_quantity >= 0', name='check_inspection_failed_non_negative'),
        CheckConstraint('passed_quantity + failed_quantity = inspected_quantity', name='check_inspection_quantities_sum'),
    )

    def __repr__(self):
        return f"<InspectionLog(plan_id={self.inspection_plan_id}, wo_id={self.work_order_id}, inspected={self.inspected_quantity})>"
