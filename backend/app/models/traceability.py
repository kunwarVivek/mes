"""
Traceability models - Lot/Batch tracking, Serial numbers, and Genealogy
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Numeric, Text, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum
from datetime import date, datetime
from typing import Optional, List, Dict
from decimal import Decimal


# Enums
class SourceType(str, Enum):
    """Source type enumeration for lot batches"""
    PURCHASED = "PURCHASED"
    MANUFACTURED = "MANUFACTURED"
    RETURNED = "RETURNED"
    ADJUSTED = "ADJUSTED"
    TRANSFERRED = "TRANSFERRED"


class QualityStatusType(str, Enum):
    """Quality status enumeration"""
    PENDING = "PENDING"
    RELEASED = "RELEASED"
    QUARANTINE = "QUARANTINE"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class SerialStatus(str, Enum):
    """Serial number status enumeration"""
    IN_STOCK = "IN_STOCK"
    RESERVED = "RESERVED"
    SHIPPED = "SHIPPED"
    INSTALLED = "INSTALLED"
    SCRAPPED = "SCRAPPED"
    RETURNED = "RETURNED"
    IN_SERVICE = "IN_SERVICE"


class EntityType(str, Enum):
    """Entity type for traceability"""
    LOT = "LOT"
    SERIAL = "SERIAL"


class RelationshipType(str, Enum):
    """Traceability relationship types"""
    CONSUMED_IN = "CONSUMED_IN"  # Component consumed in production
    ASSEMBLED_INTO = "ASSEMBLED_INTO"  # Part assembled into parent
    PACKAGED_WITH = "PACKAGED_WITH"  # Packaged together
    DERIVED_FROM = "DERIVED_FROM"  # Produced from parent
    SPLIT_FROM = "SPLIT_FROM"  # Split from parent lot
    MERGED_INTO = "MERGED_INTO"  # Merged into child lot


class OperationType(str, Enum):
    """Genealogy operation types"""
    CREATED = "CREATED"
    RECEIVED = "RECEIVED"
    INSPECTED = "INSPECTED"
    RELEASED = "RELEASED"
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    PRODUCED = "PRODUCED"
    SHIPPED = "SHIPPED"
    INSTALLED = "INSTALLED"
    RETURNED = "RETURNED"
    QUARANTINED = "QUARANTINED"
    SCRAPPED = "SCRAPPED"
    ADJUSTED = "ADJUSTED"
    TRANSFERRED = "TRANSFERRED"
    LOCATION_CHANGED = "LOCATION_CHANGED"


class LotBatch(Base):
    """
    Lot/Batch tracking model.

    Supports:
    - Lot/batch number management for materials
    - Quantity tracking with reservations
    - Quality status management
    - Expiry and retest date tracking
    - Supplier and source traceability
    - Custom traceability attributes (heat numbers, certs, etc.)
    """
    __tablename__ = 'lot_batches'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=True, index=True)

    # Lot identification
    lot_number = Column(String(100), nullable=False, index=True)
    material_id = Column(Integer, nullable=False, index=True)
    supplier_lot_number = Column(String(100), nullable=True)

    # Quantity tracking
    initial_quantity = Column(Numeric(precision=15, scale=6), nullable=False)
    current_quantity = Column(Numeric(precision=15, scale=6), nullable=False)
    reserved_quantity = Column(Numeric(precision=15, scale=6), nullable=False, default=0)
    unit_of_measure = Column(String(50), nullable=True)

    # Source information
    source_type = Column(String(50), nullable=False)  # PURCHASED, MANUFACTURED, etc.
    source_reference_id = Column(Integer, nullable=True)
    supplier_id = Column(Integer, nullable=True)

    # Dates
    production_date = Column(Date, nullable=True)
    received_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True)
    retest_date = Column(Date, nullable=True)

    # Quality status
    quality_status = Column(String(50), nullable=False, default='PENDING', index=True)
    inspection_status = Column(String(50), nullable=True)
    certificate_number = Column(String(100), nullable=True)

    # Location
    warehouse_location = Column(String(100), nullable=True)
    bin_location = Column(String(50), nullable=True)

    # Traceability attributes (heat numbers, certifications, etc.)
    traceability_attributes = Column(JSONB, nullable=True)

    # Custom attributes
    custom_attributes = Column(JSONB, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_depleted = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=False)

    # Relationships
    serial_numbers = relationship("SerialNumber", back_populates="lot_batch")
    parent_links = relationship("TraceabilityLink", foreign_keys="TraceabilityLink.parent_lot_id", back_populates="parent_lot")
    child_links = relationship("TraceabilityLink", foreign_keys="TraceabilityLink.child_lot_id", back_populates="child_lot")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'lot_number', name='uq_lot_number_per_org'),
        Index('idx_lot_batches_org', 'organization_id'),
        Index('idx_lot_batches_plant', 'plant_id'),
        Index('idx_lot_batches_material', 'material_id'),
        Index('idx_lot_batches_lot_number', 'lot_number'),
        Index('idx_lot_batches_quality_status', 'quality_status'),
        Index('idx_lot_batches_expiry', 'expiry_date'),
        CheckConstraint(
            "source_type IN ('PURCHASED', 'MANUFACTURED', 'RETURNED', 'ADJUSTED', 'TRANSFERRED')",
            name='chk_lot_source_type_valid'
        ),
        CheckConstraint(
            "quality_status IN ('PENDING', 'RELEASED', 'QUARANTINE', 'REJECTED', 'EXPIRED')",
            name='chk_lot_quality_status_valid'
        ),
        CheckConstraint('current_quantity >= 0', name='chk_lot_current_quantity_non_negative'),
        CheckConstraint('reserved_quantity >= 0', name='chk_lot_reserved_quantity_non_negative'),
    )

    def __repr__(self):
        return f"<LotBatch(id={self.id}, lot_number='{self.lot_number}', material_id={self.material_id})>"

    def get_available_quantity(self) -> Decimal:
        """Get available quantity (current - reserved)"""
        return Decimal(str(self.current_quantity)) - Decimal(str(self.reserved_quantity))

    def is_expired(self) -> bool:
        """Check if lot is expired"""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date

    def needs_retest(self) -> bool:
        """Check if lot needs retesting"""
        if not self.retest_date:
            return False
        return date.today() >= self.retest_date

    def can_be_used(self) -> bool:
        """Check if lot can be used (released, not expired, has quantity)"""
        return (
            self.quality_status == QualityStatusType.RELEASED.value and
            not self.is_expired() and
            float(self.current_quantity) > 0 and
            self.is_active
        )

    def reserve_quantity(self, quantity: float) -> bool:
        """
        Reserve quantity from the lot.

        Args:
            quantity: Amount to reserve

        Returns:
            True if successful, False if insufficient available quantity
        """
        available = float(self.get_available_quantity())
        if quantity > available:
            return False

        self.reserved_quantity = Decimal(str(float(self.reserved_quantity) + quantity))
        return True

    def consume_quantity(self, quantity: float) -> bool:
        """
        Consume quantity from the lot (reduces current and reserved).

        Args:
            quantity: Amount to consume

        Returns:
            True if successful, False if insufficient quantity
        """
        if quantity > float(self.current_quantity):
            return False

        self.current_quantity = Decimal(str(float(self.current_quantity) - quantity))

        # Also reduce reserved if applicable
        reserved = float(self.reserved_quantity)
        if reserved > 0:
            reduction = min(quantity, reserved)
            self.reserved_quantity = Decimal(str(reserved - reduction))

        # Mark as depleted if empty
        if float(self.current_quantity) == 0:
            self.is_depleted = True

        return True


class SerialNumber(Base):
    """
    Serial Number tracking model.

    Supports:
    - Individual unit serialization
    - Status and location tracking
    - Customer and shipment tracking
    - Warranty management
    - Installation and service history
    """
    __tablename__ = 'serial_numbers'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=True, index=True)

    # Serial identification
    serial_number = Column(String(100), nullable=False, index=True)
    material_id = Column(Integer, nullable=False, index=True)
    lot_batch_id = Column(Integer, ForeignKey('lot_batches.id', ondelete='SET NULL'), nullable=True, index=True)

    # Source information
    work_order_id = Column(Integer, nullable=True)
    production_date = Column(Date, nullable=True)
    production_line = Column(String(100), nullable=True)

    # Status and location
    status = Column(String(50), nullable=False, default='IN_STOCK', index=True)
    quality_status = Column(String(50), nullable=False, default='PENDING')
    current_location = Column(String(200), nullable=True)
    warehouse_location = Column(String(100), nullable=True)

    # Customer/shipment tracking
    customer_id = Column(Integer, nullable=True, index=True)
    shipment_id = Column(Integer, nullable=True)
    shipped_date = Column(Date, nullable=True)
    installation_date = Column(Date, nullable=True)
    installation_location = Column(String(200), nullable=True)

    # Warranty and service
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    last_service_date = Column(Date, nullable=True)

    # Traceability attributes
    traceability_attributes = Column(JSONB, nullable=True)

    # Custom attributes
    custom_attributes = Column(JSONB, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=False)

    # Relationships
    lot_batch = relationship("LotBatch", back_populates="serial_numbers")
    parent_links = relationship("TraceabilityLink", foreign_keys="TraceabilityLink.parent_serial_id", back_populates="parent_serial")
    child_links = relationship("TraceabilityLink", foreign_keys="TraceabilityLink.child_serial_id", back_populates="child_serial")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'serial_number', name='uq_serial_number_per_org'),
        Index('idx_serial_numbers_org', 'organization_id'),
        Index('idx_serial_numbers_plant', 'plant_id'),
        Index('idx_serial_numbers_material', 'material_id'),
        Index('idx_serial_numbers_lot', 'lot_batch_id'),
        Index('idx_serial_numbers_serial', 'serial_number'),
        Index('idx_serial_numbers_status', 'status'),
        Index('idx_serial_numbers_customer', 'customer_id'),
        CheckConstraint(
            "status IN ('IN_STOCK', 'RESERVED', 'SHIPPED', 'INSTALLED', 'SCRAPPED', 'RETURNED', 'IN_SERVICE')",
            name='chk_serial_status_valid'
        ),
        CheckConstraint(
            "quality_status IN ('PENDING', 'RELEASED', 'QUARANTINE', 'REJECTED')",
            name='chk_serial_quality_status_valid'
        ),
    )

    def __repr__(self):
        return f"<SerialNumber(id={self.id}, serial='{self.serial_number}', status='{self.status}')>"

    def is_in_warranty(self) -> bool:
        """Check if serial is currently under warranty"""
        if not self.warranty_end_date:
            return False
        return date.today() <= self.warranty_end_date

    def is_available(self) -> bool:
        """Check if serial is available for use/shipment"""
        return (
            self.status == SerialStatus.IN_STOCK.value and
            self.quality_status == QualityStatusType.RELEASED.value and
            self.is_active
        )

    def get_age_days(self) -> Optional[int]:
        """Get age in days since production"""
        if not self.production_date:
            return None
        return (date.today() - self.production_date).days


class TraceabilityLink(Base):
    """
    Traceability Link model.

    Links parent entities (components/materials) to child entities (products).
    Supports both lot-to-lot and serial-to-serial relationships.
    """
    __tablename__ = 'traceability_links'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Parent (what was used/consumed)
    parent_type = Column(String(20), nullable=False)  # LOT, SERIAL
    parent_lot_id = Column(Integer, ForeignKey('lot_batches.id', ondelete='CASCADE'), nullable=True, index=True)
    parent_serial_id = Column(Integer, ForeignKey('serial_numbers.id', ondelete='CASCADE'), nullable=True, index=True)

    # Child (what was produced/created)
    child_type = Column(String(20), nullable=False)  # LOT, SERIAL
    child_lot_id = Column(Integer, ForeignKey('lot_batches.id', ondelete='CASCADE'), nullable=True, index=True)
    child_serial_id = Column(Integer, ForeignKey('serial_numbers.id', ondelete='CASCADE'), nullable=True, index=True)

    # Relationship details
    relationship_type = Column(String(50), nullable=False)
    quantity_used = Column(Numeric(precision=15, scale=6), nullable=True)
    unit_of_measure = Column(String(50), nullable=True)

    # Context
    work_order_id = Column(Integer, nullable=True, index=True)
    operation_sequence = Column(Integer, nullable=True)
    link_date = Column(DateTime(timezone=True), nullable=False, index=True)

    # Additional metadata
    metadata = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, nullable=False)

    # Relationships
    parent_lot = relationship("LotBatch", foreign_keys=[parent_lot_id], back_populates="child_links")
    parent_serial = relationship("SerialNumber", foreign_keys=[parent_serial_id], back_populates="child_links")
    child_lot = relationship("LotBatch", foreign_keys=[child_lot_id], back_populates="parent_links")
    child_serial = relationship("SerialNumber", foreign_keys=[child_serial_id], back_populates="parent_links")

    # Table constraints
    __table_args__ = (
        Index('idx_traceability_links_org', 'organization_id'),
        Index('idx_traceability_links_parent_lot', 'parent_lot_id'),
        Index('idx_traceability_links_parent_serial', 'parent_serial_id'),
        Index('idx_traceability_links_child_lot', 'child_lot_id'),
        Index('idx_traceability_links_child_serial', 'child_serial_id'),
        Index('idx_traceability_links_wo', 'work_order_id'),
        Index('idx_traceability_links_date', 'link_date'),
        CheckConstraint(
            "parent_type IN ('LOT', 'SERIAL')",
            name='chk_parent_type_valid'
        ),
        CheckConstraint(
            "child_type IN ('LOT', 'SERIAL')",
            name='chk_child_type_valid'
        ),
        CheckConstraint(
            "relationship_type IN ('CONSUMED_IN', 'ASSEMBLED_INTO', 'PACKAGED_WITH', 'DERIVED_FROM', 'SPLIT_FROM', 'MERGED_INTO')",
            name='chk_relationship_type_valid'
        ),
        CheckConstraint(
            "(parent_type = 'LOT' AND parent_lot_id IS NOT NULL) OR (parent_type = 'SERIAL' AND parent_serial_id IS NOT NULL)",
            name='chk_parent_reference_valid'
        ),
        CheckConstraint(
            "(child_type = 'LOT' AND child_lot_id IS NOT NULL) OR (child_type = 'SERIAL' AND child_serial_id IS NOT NULL)",
            name='chk_child_reference_valid'
        ),
    )

    def __repr__(self):
        return f"<TraceabilityLink(id={self.id}, {self.parent_type}->{self.child_type}, type='{self.relationship_type}')>"


class GenealogyRecord(Base):
    """
    Genealogy Record model (TimescaleDB hypertable).

    Complete audit trail for all lot and serial number operations.
    Provides full genealogy/pedigree tracking with time-series storage.
    """
    __tablename__ = 'genealogy_records'

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Entity being tracked
    entity_type = Column(String(20), nullable=False)  # LOT, SERIAL
    entity_id = Column(Integer, nullable=False)
    entity_identifier = Column(String(100), nullable=False, index=True)  # Lot number or serial number

    # Operation details
    operation_type = Column(String(50), nullable=False, index=True)
    operation_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Context
    work_order_id = Column(Integer, nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)

    # Quantity changes (for lots)
    quantity_before = Column(Numeric(precision=15, scale=6), nullable=True)
    quantity_after = Column(Numeric(precision=15, scale=6), nullable=True)
    quantity_change = Column(Numeric(precision=15, scale=6), nullable=True)

    # Status changes
    status_before = Column(String(50), nullable=True)
    status_after = Column(String(50), nullable=True)

    # Location changes
    location_before = Column(String(200), nullable=True)
    location_after = Column(String(200), nullable=True)

    # Metadata
    metadata = Column(JSONB, nullable=True)

    # Audit
    performed_by = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Table constraints
    __table_args__ = (
        Index('idx_genealogy_records_org', 'organization_id'),
        Index('idx_genealogy_records_entity', 'entity_type', 'entity_id'),
        Index('idx_genealogy_records_identifier', 'entity_identifier'),
        Index('idx_genealogy_records_timestamp', 'operation_timestamp'),
        Index('idx_genealogy_records_operation', 'operation_type'),
        CheckConstraint(
            "entity_type IN ('LOT', 'SERIAL')",
            name='chk_genealogy_entity_type_valid'
        ),
    )

    def __repr__(self):
        return f"<GenealogyRecord(id={self.id}, {self.entity_type}:{self.entity_identifier}, op='{self.operation_type}')>"
