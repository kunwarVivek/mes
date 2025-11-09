"""
SQLAlchemy models for Material Management domain.
Phase 2: Material Master Data
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class DimensionType(str, enum.Enum):
    """Enum for unit of measure dimensions"""
    LENGTH = "LENGTH"
    MASS = "MASS"
    VOLUME = "VOLUME"
    TIME = "TIME"
    QUANTITY = "QUANTITY"


class ProcurementType(str, enum.Enum):
    """Enum for material procurement types"""
    PURCHASE = "PURCHASE"
    MANUFACTURE = "MANUFACTURE"
    BOTH = "BOTH"


class MRPType(str, enum.Enum):
    """Enum for MRP planning types"""
    MRP = "MRP"
    REORDER = "REORDER"


class LotSizingRule(str, enum.Enum):
    """Enum for lot sizing rules"""
    LOT_FOR_LOT = "LOT_FOR_LOT"
    FIXED_LOT_SIZE = "FIXED_LOT_SIZE"
    EOQ = "EOQ"
    POQ = "POQ"


class POQPeriodType(str, enum.Enum):
    """Enum for POQ period types"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class UnitOfMeasure(Base):
    """
    Unit of Measure entity - defines measurement units for materials.

    Supports conversion between units within the same dimension.
    Base units have conversion_factor = 1.0
    """
    __tablename__ = "unit_of_measure"

    id = Column(Integer, primary_key=True, index=True)
    uom_code = Column(String(10), unique=True, nullable=False, index=True)
    uom_name = Column(String(100), nullable=False)
    dimension = Column(Enum(DimensionType), nullable=False)
    is_base_unit = Column(Boolean, default=False, nullable=False)
    conversion_factor = Column(Float, nullable=False)  # Factor to convert to base unit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    materials = relationship("Material", back_populates="base_uom")

    def __repr__(self):
        return f"<UnitOfMeasure(code='{self.uom_code}', name='{self.uom_name}', dimension='{self.dimension}')>"


class MaterialCategory(Base):
    """
    Material Category entity - hierarchical classification of materials.

    Supports parent-child relationships for multi-level categorization.
    Category codes must be unique within an organization.
    """
    __tablename__ = "material_category"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    category_code = Column(String(20), nullable=False, index=True)
    category_name = Column(String(100), nullable=False)
    parent_category_id = Column(Integer, ForeignKey('material_category.id', ondelete='CASCADE'), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Self-referential relationship for hierarchy
    parent = relationship("MaterialCategory", remote_side=[id], backref="children")

    # Relationships
    materials = relationship("Material", back_populates="category")

    # Unique constraint: category_code per organization
    __table_args__ = (
        UniqueConstraint('organization_id', 'category_code', name='uq_category_code_per_org'),
        Index('idx_material_category_org_code', 'organization_id', 'category_code'),
    )

    def __repr__(self):
        return f"<MaterialCategory(code='{self.category_code}', name='{self.category_name}', org={self.organization_id})>"


class Material(Base):
    """
    Material entity - master data for materials used in manufacturing.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Links to category and base unit of measure.
    Includes MRP planning parameters (safety stock, reorder point, lead time).
    """
    __tablename__ = "material"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    material_number = Column(String(10), unique=True, nullable=False, index=True)
    material_name = Column(String(200), nullable=False)
    description = Column(String(500))
    material_category_id = Column(Integer, ForeignKey('material_category.id', ondelete='CASCADE'), nullable=False)
    base_uom_id = Column(Integer, ForeignKey('unit_of_measure.id', ondelete='CASCADE'), nullable=False)
    procurement_type = Column(Enum(ProcurementType), nullable=False)
    mrp_type = Column(Enum(MRPType), nullable=False)
    safety_stock = Column(Float, nullable=False, default=0.0)
    reorder_point = Column(Float, nullable=False, default=0.0)
    lot_size = Column(Float, nullable=False, default=1.0)
    lead_time_days = Column(Integer, nullable=False, default=0)

    # Lot sizing configuration
    lot_sizing_rule = Column(Enum(LotSizingRule), nullable=False, default=LotSizingRule.LOT_FOR_LOT)
    fixed_lot_size = Column(Float, nullable=True)  # For FIXED_LOT_SIZE rule
    poq_period_type = Column(Enum(POQPeriodType), nullable=True)  # For POQ rule
    poq_periods_to_cover = Column(Integer, nullable=True)  # For POQ rule

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("MaterialCategory", back_populates="materials")
    base_uom = relationship("UnitOfMeasure", back_populates="materials")

    # Indexes for RLS and common queries
    __table_args__ = (
        Index('idx_material_org_plant', 'organization_id', 'plant_id'),
        Index('idx_material_category', 'material_category_id'),
        Index('idx_material_number', 'material_number'),
    )

    def __repr__(self):
        return f"<Material(number='{self.material_number}', name='{self.material_name}', org={self.organization_id}, plant={self.plant_id})>"
