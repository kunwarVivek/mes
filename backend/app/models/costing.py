"""
SQLAlchemy models for Material Costing domain.
Phase 2: Material Management - Material Costing

Supports FIFO, LIFO, Weighted Average, and Standard costing methods.
Multi-currency support with exchange rate management.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Enum, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from decimal import Decimal
import enum


# Import Currency for relationship (deferred import to avoid circular dependency)
def _get_currency_class():
    from app.models.currency import Currency
    return Currency


class CostingMethod(str, enum.Enum):
    """Enum for material costing methods"""
    FIFO = "FIFO"  # First In First Out
    LIFO = "LIFO"  # Last In First Out
    WEIGHTED_AVERAGE = "WEIGHTED_AVERAGE"  # Moving weighted average
    STANDARD = "STANDARD"  # Standard cost


class MaterialCosting(Base):
    """
    Material Costing entity - defines costing method and costs for materials.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    One costing record per material per plant (unique constraint).
    Different costing methods: FIFO, LIFO, WEIGHTED_AVERAGE, STANDARD.
    Multi-currency support: Costs stored in specified currency.
    """
    __tablename__ = "material_costing"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    costing_method = Column(Enum(CostingMethod), nullable=False)
    currency_code = Column(String(3), ForeignKey('currency.code'), nullable=False, index=True)
    standard_cost = Column(Numeric(15, 2), nullable=True)  # For STANDARD method
    current_average_cost = Column(Numeric(15, 2), nullable=True)  # For WEIGHTED_AVERAGE method
    last_cost_update_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    material = relationship("Material", backref="costing_records")
    currency = relationship("Currency", backref="material_costings")

    # Constraints and indexes
    __table_args__ = (
        # Check constraints for cost validations
        CheckConstraint('standard_cost >= 0 OR standard_cost IS NULL', name='chk_standard_cost_non_negative'),
        CheckConstraint('current_average_cost >= 0 OR current_average_cost IS NULL', name='chk_avg_cost_non_negative'),

        # Unique constraint: one costing record per material per plant
        UniqueConstraint(
            'organization_id', 'plant_id', 'material_id',
            name='uq_costing_per_material_per_plant'
        ),

        # Indexes for RLS and common queries
        Index('idx_material_costing_org_plant', 'organization_id', 'plant_id'),
        Index('idx_material_costing_material', 'material_id'),
        Index('idx_material_costing_currency', 'currency_code'),
    )

    def __repr__(self):
        return f"<MaterialCosting(material_id={self.material_id}, method='{self.costing_method}', org={self.organization_id}, plant={self.plant_id})>"


class CostLayer(Base):
    """
    Cost Layer entity - tracks inventory layers for FIFO/LIFO costing.

    Each receipt creates a cost layer with quantity and unit cost.
    As inventory is issued, quantity_remaining is decreased (FIFO/LIFO rules).
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Multi-currency support: Unit costs stored in specified currency.
    """
    __tablename__ = "cost_layer"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    storage_location_id = Column(Integer, ForeignKey('storage_location.id', ondelete='CASCADE'), nullable=False, index=True)
    batch_number = Column(String(50), nullable=False)
    quantity_received = Column(Numeric(15, 3), nullable=False)
    quantity_remaining = Column(Numeric(15, 3), nullable=False)
    unit_cost = Column(Numeric(15, 2), nullable=False)
    currency_code = Column(String(3), ForeignKey('currency.code'), nullable=False, index=True)
    receipt_date = Column(DateTime(timezone=True), nullable=False, index=True)
    transaction_reference = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    material = relationship("Material", backref="cost_layers")
    storage_location = relationship("StorageLocation", backref="cost_layers")
    currency = relationship("Currency", backref="cost_layers")

    # Constraints and indexes
    __table_args__ = (
        # Check constraints for quantity validations
        CheckConstraint('quantity_remaining >= 0', name='chk_quantity_remaining_non_negative'),
        CheckConstraint('quantity_remaining <= quantity_received', name='chk_remaining_not_exceed_received'),
        CheckConstraint('quantity_received > 0', name='chk_quantity_received_positive'),
        CheckConstraint('unit_cost >= 0', name='chk_unit_cost_non_negative'),

        # Indexes for FIFO (oldest first) and LIFO (newest first) queries
        Index('idx_cost_layer_fifo', 'material_id', 'receipt_date'),  # ASC for FIFO
        Index('idx_cost_layer_lifo', 'material_id', 'receipt_date'),  # DESC for LIFO (handled in query)
        Index('idx_cost_layer_org_plant', 'organization_id', 'plant_id'),
        Index('idx_cost_layer_material', 'material_id'),
        Index('idx_cost_layer_currency', 'currency_code'),
    )

    def consume_quantity(self, quantity: Decimal) -> None:
        """
        Business logic: Consume quantity from this cost layer.

        Args:
            quantity: Amount to consume from this layer

        Raises:
            ValueError: If insufficient remaining quantity
        """
        if quantity > self.quantity_remaining:
            raise ValueError(
                f"Insufficient remaining quantity. Available: {self.quantity_remaining}, Requested: {quantity}"
            )
        self.quantity_remaining -= quantity

    def __repr__(self):
        return f"<CostLayer(material_id={self.material_id}, batch='{self.batch_number}', remaining={self.quantity_remaining}, cost={self.unit_cost})>"
