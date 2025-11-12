"""Quality Inspection models for in-process quality checks."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class QualityInspection(Base):
    """Quality inspection model for in-process, final, and incoming inspections."""

    __tablename__ = "quality_inspections"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=True, index=True)
    inspection_type = Column(String(50), nullable=False, index=True)  # in_process, final, incoming, first_article
    inspection_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    inspector_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    result = Column(String(50), nullable=False, index=True)  # passed, failed, conditional, pending
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="quality_inspections")
    plant = relationship("Plant", back_populates="quality_inspections")
    work_order = relationship("WorkOrder", back_populates="quality_inspections")
    material = relationship("Material", back_populates="quality_inspections")
    inspector = relationship("User", foreign_keys=[inspector_id])
    checkpoints = relationship("QualityCheckpoint", back_populates="inspection", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "inspection_type IN ('in_process', 'final', 'incoming', 'first_article')",
            name='ck_quality_inspections_type'
        ),
        CheckConstraint(
            "result IN ('passed', 'failed', 'conditional', 'pending')",
            name='ck_quality_inspections_result'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<QualityInspection(id={self.id}, type='{self.inspection_type}', result='{self.result}')>"

    @property
    def passed(self) -> bool:
        """Check if inspection passed."""
        return self.result == 'passed'

    @property
    def failed(self) -> bool:
        """Check if inspection failed."""
        return self.result == 'failed'


class QualityCheckpoint(Base):
    """Individual checkpoint within a quality inspection."""

    __tablename__ = "quality_checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    inspection_id = Column(Integer, ForeignKey("quality_inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    checkpoint_name = Column(String(255), nullable=False)
    characteristic = Column(String(255), nullable=True)  # e.g., "Length", "Diameter", "Hardness"
    specification = Column(String(255), nullable=True)  # e.g., "100mm ± 0.5mm"
    expected_value = Column(String(100), nullable=True)  # Expected measurement
    actual_value = Column(String(100), nullable=True)  # Actual measurement
    uom = Column(String(50), nullable=True)  # Unit of measure (mm, kg, etc.)
    result = Column(String(50), nullable=False, index=True)  # passed, failed, within_tolerance, out_of_spec, not_measured
    notes = Column(Text, nullable=True)
    measured_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization")
    inspection = relationship("QualityInspection", back_populates="checkpoints")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "result IN ('passed', 'failed', 'within_tolerance', 'out_of_spec', 'not_measured')",
            name='ck_quality_checkpoints_result'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<QualityCheckpoint(id={self.id}, name='{self.checkpoint_name}', result='{self.result}')>"

    @property
    def passed(self) -> bool:
        """Check if checkpoint passed."""
        return self.result in ('passed', 'within_tolerance')
