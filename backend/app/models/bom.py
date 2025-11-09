"""
SQLAlchemy models for BOM (Bill of Materials) domain.
Phase 3: Production Planning Module - Component 2
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey, Enum, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class BOMType(str, enum.Enum):
    """Enum for BOM types"""
    PRODUCTION = "PRODUCTION"
    ENGINEERING = "ENGINEERING"
    PLANNING = "PLANNING"


class BOMHeader(Base):
    """
    BOM Header entity - defines what components/materials are needed to produce a finished good.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Version control for engineering changes (bom_version).
    Links to Material entity for the finished good being produced.
    """
    __tablename__ = "bom_header"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    bom_number = Column(String(50), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    bom_version = Column(Integer, nullable=False, default=1)
    bom_name = Column(String(200), nullable=False)
    bom_type = Column(Enum(BOMType), nullable=False)
    base_quantity = Column(Float, nullable=False)
    unit_of_measure_id = Column(Integer, ForeignKey('unit_of_measure.id', ondelete='CASCADE'), nullable=False)
    # Effectivity date fields for BOM lifecycle management
    effective_start_date = Column(Date, nullable=True, index=True)  # Nullable for legacy BOMs
    effective_end_date = Column(Date, nullable=True)  # Nullable for open-ended BOMs
    is_active = Column(Boolean, default=True, nullable=False, index=True)  # Manual activation control
    created_by_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    material = relationship("Material", backref="bom_headers")
    unit_of_measure = relationship("UnitOfMeasure")
    bom_lines = relationship("BOMLine", back_populates="bom_header", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="bom")

    # Unique constraint: (organization_id, plant_id, material_id, bom_version)
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id', 'material_id', 'bom_version',
                         name='uq_bom_per_material_version'),
        Index('idx_bom_header_org_plant', 'organization_id', 'plant_id'),
        Index('idx_bom_header_material', 'material_id'),
        Index('idx_bom_header_bom_number', 'bom_number'),
        Index('idx_bom_header_effectivity', 'material_id', 'effective_start_date', 'effective_end_date'),
        CheckConstraint('base_quantity > 0', name='check_base_quantity_positive'),
        CheckConstraint('bom_version >= 1', name='check_bom_version_minimum'),
        CheckConstraint(
            'effective_end_date IS NULL OR effective_start_date IS NULL OR effective_start_date <= effective_end_date',
            name='check_effective_dates_valid'
        ),
    )

    def __repr__(self):
        return f"<BOMHeader(bom_number='{self.bom_number}', version={self.bom_version}, material_id={self.material_id})>"


class BOMLine(Base):
    """
    BOM Line entity - defines individual material components required for production.

    Represents a single component in a BOM (e.g., 2 units of Material B needed).
    Supports phantom BOMs (exploded during planning) and backflush (auto-consume).
    Links to Material entity for the input material.
    """
    __tablename__ = "bom_line"

    id = Column(Integer, primary_key=True)
    bom_header_id = Column(Integer, ForeignKey('bom_header.id', ondelete='CASCADE'), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    component_material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit_of_measure_id = Column(Integer, ForeignKey('unit_of_measure.id', ondelete='CASCADE'), nullable=False)
    scrap_factor = Column(Float, nullable=False, default=0.0)
    operation_number = Column(Integer, nullable=True)
    is_phantom = Column(Boolean, default=False, nullable=False)
    backflush = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bom_header = relationship("BOMHeader", back_populates="bom_lines")
    component_material = relationship("Material", foreign_keys=[component_material_id])
    unit_of_measure = relationship("UnitOfMeasure")

    # Unique constraint: (bom_header_id, line_number)
    __table_args__ = (
        UniqueConstraint('bom_header_id', 'line_number',
                         name='uq_line_number_per_bom'),
        Index('idx_bom_line_bom_header', 'bom_header_id'),
        Index('idx_bom_line_component_material', 'component_material_id'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('scrap_factor >= 0 AND scrap_factor <= 100', name='check_scrap_factor_range'),
        CheckConstraint('line_number > 0', name='check_line_number_positive'),
    )

    def __repr__(self):
        return f"<BOMLine(bom_header_id={self.bom_header_id}, line_num={self.line_number}, component_mat_id={self.component_material_id})>"
