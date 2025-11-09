"""
SQLAlchemy models for Quality Management - NCR domain.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, Index, CheckConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class NCRStatus(str, enum.Enum):
    """Enum for NCR status"""
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class DefectType(str, enum.Enum):
    """Enum for defect types"""
    DIMENSIONAL = "DIMENSIONAL"
    VISUAL = "VISUAL"
    FUNCTIONAL = "FUNCTIONAL"
    MATERIAL = "MATERIAL"
    OTHER = "OTHER"


class NCR(Base):
    """
    Non-Conformance Report (NCR) entity.

    Tracks quality issues and defects during production.
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Links to Work Order and Material entities.
    """
    __tablename__ = "ncr"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    ncr_number = Column(String(50), nullable=False, index=True)
    work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='CASCADE'), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    defect_type = Column(Enum(DefectType), nullable=False)
    defect_description = Column(String(500), nullable=False)
    quantity_defective = Column(Float, nullable=False)
    status = Column(Enum(NCRStatus), nullable=False, default=NCRStatus.OPEN, index=True)
    reported_by_user_id = Column(Integer, nullable=False)
    attachment_urls = Column(JSON, nullable=True)  # Array of MinIO URLs
    resolution_notes = Column(String(1000), nullable=True)
    resolved_by_user_id = Column(Integer, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    work_order = relationship("WorkOrder", backref="ncrs")
    material = relationship("Material", backref="ncrs")

    # Constraints
    __table_args__ = (
        Index('idx_ncr_org_plant', 'organization_id', 'plant_id'),
        Index('idx_ncr_work_order', 'work_order_id'),
        Index('idx_ncr_status', 'status'),
        CheckConstraint('quantity_defective > 0', name='check_ncr_quantity_positive'),
    )

    def __repr__(self):
        return f"<NCR(number='{self.ncr_number}', status='{self.status}', org={self.organization_id})>"
