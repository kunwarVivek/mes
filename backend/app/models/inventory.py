"""
SQLAlchemy models for Inventory Management domain.
Phase 2: Material Management - Inventory Tracking
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class LocationType(str, enum.Enum):
    """Enum for storage location types"""
    WAREHOUSE = "WAREHOUSE"
    PRODUCTION = "PRODUCTION"
    QUALITY = "QUALITY"
    BLOCKED = "BLOCKED"


class TransactionType(str, enum.Enum):
    """Enum for inventory transaction types"""
    GOODS_RECEIPT = "GOODS_RECEIPT"
    GOODS_ISSUE = "GOODS_ISSUE"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    ADJUSTMENT = "ADJUSTMENT"


class StorageLocation(Base):
    """
    Storage Location entity - defines warehouse locations for inventory storage.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Location codes are unique within a plant.
    """
    __tablename__ = "storage_location"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    location_code = Column(String(20), nullable=False, index=True)
    location_name = Column(String(100), nullable=False)
    location_type = Column(Enum(LocationType), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    inventory_records = relationship("Inventory", back_populates="storage_location")
    transactions = relationship("InventoryTransaction", back_populates="storage_location")

    # Unique constraint: location_code per plant
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id', 'location_code', name='uq_location_code_per_plant'),
        Index('idx_storage_location_org_plant', 'organization_id', 'plant_id'),
    )

    def __repr__(self):
        return f"<StorageLocation(code='{self.location_code}', name='{self.location_name}', type='{self.location_type}')>"


class Inventory(Base):
    """
    Inventory entity - tracks material quantities at storage locations.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Composite unique constraint ensures one record per (org, plant, material, location, batch).
    Computed quantity_available = quantity_on_hand - quantity_reserved.
    """
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    storage_location_id = Column(Integer, ForeignKey('storage_location.id', ondelete='CASCADE'), nullable=False, index=True)
    batch_number = Column(String(50), nullable=False)
    quantity_on_hand = Column(Float, nullable=False, default=0.0)
    quantity_reserved = Column(Float, nullable=False, default=0.0)
    unit_of_measure_id = Column(Integer, ForeignKey('unit_of_measure.id', ondelete='CASCADE'), nullable=False)
    last_movement_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Computed column: quantity_available = quantity_on_hand - quantity_reserved
    quantity_available = column_property(quantity_on_hand - quantity_reserved)

    # Relationships
    material = relationship("Material", backref="inventory_records")
    storage_location = relationship("StorageLocation", back_populates="inventory_records")
    unit_of_measure = relationship("UnitOfMeasure")

    # Constraints and indexes
    __table_args__ = (
        # Check constraints for quantities
        CheckConstraint('quantity_on_hand >= 0', name='chk_quantity_on_hand_non_negative'),
        CheckConstraint('quantity_reserved >= 0', name='chk_quantity_reserved_non_negative'),
        CheckConstraint('quantity_reserved <= quantity_on_hand', name='chk_reserved_not_exceed_on_hand'),

        # Composite unique constraint
        UniqueConstraint(
            'organization_id', 'plant_id', 'material_id', 'storage_location_id', 'batch_number',
            name='uq_inventory_composite'
        ),

        # Indexes for RLS and common queries
        Index('idx_inventory_org_plant', 'organization_id', 'plant_id'),
        Index('idx_inventory_org_plant_material', 'organization_id', 'plant_id', 'material_id'),
        Index('idx_inventory_storage_location', 'storage_location_id'),
    )

    def reserve_quantity(self, quantity: float) -> None:
        """
        Business logic: Reserve quantity for production or sales orders.

        Args:
            quantity: Amount to reserve

        Raises:
            ValueError: If insufficient available quantity
        """
        available = self.quantity_on_hand - self.quantity_reserved
        if quantity > available:
            raise ValueError(
                f"Insufficient available quantity. Available: {available}, Requested: {quantity}"
            )
        self.quantity_reserved += quantity

    def release_reserved_quantity(self, quantity: float) -> None:
        """
        Business logic: Release previously reserved quantity.

        Args:
            quantity: Amount to release

        Raises:
            ValueError: If trying to release more than reserved
        """
        if quantity > self.quantity_reserved:
            raise ValueError(
                f"Cannot release more than reserved. Reserved: {self.quantity_reserved}, Requested: {quantity}"
            )
        self.quantity_reserved -= quantity

    def update_quantity(self, new_quantity: float) -> None:
        """
        Business logic: Update quantity on hand.

        Args:
            new_quantity: New quantity on hand

        Raises:
            ValueError: If new quantity is negative
        """
        if new_quantity < 0:
            raise ValueError("Quantity on hand cannot be negative")
        self.quantity_on_hand = new_quantity
        self.last_movement_date = func.now()

    def __repr__(self):
        return f"<Inventory(material_id={self.material_id}, location={self.storage_location_id}, on_hand={self.quantity_on_hand}, reserved={self.quantity_reserved})>"


class InventoryTransaction(Base):
    """
    Inventory Transaction entity - immutable audit trail of inventory movements.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Transactions are immutable (no updated_at field).
    Quantity sign: positive for receipts/transfers_in, negative for issues/transfers_out.
    """
    __tablename__ = "inventory_transaction"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    storage_location_id = Column(Integer, ForeignKey('storage_location.id', ondelete='CASCADE'), nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    transaction_reference = Column(String(100), nullable=False)  # PO, WO, etc.
    batch_number = Column(String(50), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_of_measure_id = Column(Integer, ForeignKey('unit_of_measure.id', ondelete='CASCADE'), nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    posted_by_user_id = Column(Integer, nullable=False)
    notes = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    material = relationship("Material")
    storage_location = relationship("StorageLocation", back_populates="transactions")
    unit_of_measure = relationship("UnitOfMeasure")

    # Indexes for reporting and queries
    __table_args__ = (
        Index('idx_transaction_org_plant', 'organization_id', 'plant_id'),
        Index('idx_transaction_material', 'material_id'),
        Index('idx_transaction_date', 'transaction_date'),
        Index('idx_transaction_type', 'transaction_type'),
        Index('idx_transaction_date_type', 'transaction_date', 'transaction_type'),
    )

    def __repr__(self):
        return f"<InventoryTransaction(type='{self.transaction_type}', material_id={self.material_id}, qty={self.quantity}, date={self.transaction_date})>"
