"""
SQLAlchemy models for Logistics Module domain.
Phase: Logistics & Shipment Tracking - Barcode/QR Integration
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, UniqueConstraint, Index, CheckConstraint, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime, timedelta
from typing import Optional


class ShipmentType(str, enum.Enum):
    """Enum for shipment types"""
    INBOUND = "INBOUND"  # Incoming materials/goods
    OUTBOUND = "OUTBOUND"  # Outgoing finished goods
    TRANSFER = "TRANSFER"  # Inter-plant transfer
    RETURN = "RETURN"  # Customer/supplier returns


class ShipmentStatus(str, enum.Enum):
    """Enum for shipment status"""
    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    DELAYED = "DELAYED"


class BarcodeType(str, enum.Enum):
    """Enum for barcode types"""
    CODE128 = "CODE128"
    CODE39 = "CODE39"
    EAN13 = "EAN13"
    UPC_A = "UPC_A"
    QR_CODE = "QR_CODE"
    DATA_MATRIX = "DATA_MATRIX"


class ScanResolution(str, enum.Enum):
    """Enum for scan resolution/outcome"""
    SUCCESS = "SUCCESS"  # Successfully identified entity
    PARTIAL = "PARTIAL"  # Identified but missing data
    ERROR = "ERROR"  # Invalid or unrecognized code
    DUPLICATE = "DUPLICATE"  # Already scanned
    NOT_FOUND = "NOT_FOUND"  # Code not in system


class Shipment(Base):
    """
    Shipment entity - tracks inbound/outbound shipments.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Tracks shipment lifecycle from planning through delivery.
    Links to carrier, origin, and destination information.
    """
    __tablename__ = "shipment"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    shipment_number = Column(String(50), nullable=False, index=True)
    shipment_type = Column(Enum(ShipmentType), nullable=False, index=True)
    shipment_status = Column(Enum(ShipmentStatus), nullable=False, default=ShipmentStatus.DRAFT, index=True)

    # Carrier and tracking
    carrier_name = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True, index=True)

    # Origin and destination
    origin_location = Column(String(200), nullable=True)
    destination_location = Column(String(200), nullable=True)

    # Dates
    planned_ship_date = Column(DateTime(timezone=True), nullable=True)
    actual_ship_date = Column(DateTime(timezone=True), nullable=True)
    planned_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)

    # Weight and dimensions
    total_weight = Column(Float, nullable=False, default=0.0)
    weight_uom = Column(String(10), nullable=False, default="KG")
    total_volume = Column(Float, nullable=False, default=0.0)
    volume_uom = Column(String(10), nullable=False, default="M3")

    # Cost tracking
    freight_cost = Column(Float, nullable=False, default=0.0)
    currency_code = Column(String(3), nullable=False, default="USD")

    # References
    reference_document_type = Column(String(50), nullable=True)  # PO, WO, SO, etc.
    reference_document_id = Column(Integer, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Audit
    created_by_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    items = relationship("ShipmentItem", back_populates="shipment", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id', 'shipment_number',
                         name='uq_shipment_number_per_plant'),
        Index('idx_shipment_org_plant', 'organization_id', 'plant_id'),
        Index('idx_shipment_status', 'shipment_status'),
        Index('idx_shipment_type', 'shipment_type'),
        Index('idx_shipment_tracking', 'tracking_number'),
        Index('idx_shipment_planned_delivery', 'planned_delivery_date'),
        CheckConstraint('total_weight >= 0', name='chk_shipment_weight_non_negative'),
        CheckConstraint('total_volume >= 0', name='chk_shipment_volume_non_negative'),
        CheckConstraint('freight_cost >= 0', name='chk_shipment_cost_non_negative'),
    )

    def calculate_total_weight(self) -> float:
        """
        Calculate total weight from all shipment items.

        Returns:
            Total weight across all items (assumes items use same UOM)
        """
        if not self.items:
            return 0.0
        return sum(item.weight * item.quantity for item in self.items if item.weight)

    def is_overdue(self) -> bool:
        """
        Check if shipment is overdue based on planned delivery date.

        Returns:
            True if past planned delivery date and not yet delivered
        """
        if not self.planned_delivery_date:
            return False

        if self.shipment_status in [ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED]:
            return False

        return datetime.now(self.planned_delivery_date.tzinfo) > self.planned_delivery_date

    def __repr__(self):
        return f"<Shipment(number='{self.shipment_number}', type='{self.shipment_type}', status='{self.shipment_status}')>"


class ShipmentItem(Base):
    """
    Shipment Item entity - line items within a shipment.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Each item can have barcodes/QR codes generated for tracking.
    Links to Material for inventory integration.
    """
    __tablename__ = "shipment_item"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    shipment_id = Column(Integer, ForeignKey('shipment.id', ondelete='CASCADE'), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)

    # Material reference
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=True, index=True)
    material_description = Column(String(200), nullable=True)

    # Quantity
    quantity = Column(Float, nullable=False)
    unit_of_measure_id = Column(Integer, ForeignKey('unit_of_measure.id', ondelete='CASCADE'), nullable=False)

    # Batch/lot tracking
    batch_number = Column(String(50), nullable=True)
    serial_number = Column(String(50), nullable=True)

    # Physical attributes
    weight = Column(Float, nullable=True)
    weight_uom = Column(String(10), nullable=True)
    volume = Column(Float, nullable=True)
    volume_uom = Column(String(10), nullable=True)

    # Packaging
    package_id = Column(String(50), nullable=True, index=True)
    package_type = Column(String(50), nullable=True)

    # Barcode reference (generated separately)
    barcode_value = Column(String(100), nullable=True, index=True)
    barcode_type = Column(Enum(BarcodeType), nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shipment = relationship("Shipment", back_populates="items")
    material = relationship("Material")
    unit_of_measure = relationship("UnitOfMeasure")
    labels = relationship("BarcodeLabel", back_populates="shipment_item", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('shipment_id', 'line_number',
                         name='uq_line_number_per_shipment'),
        Index('idx_shipment_item_org_plant', 'organization_id', 'plant_id'),
        Index('idx_shipment_item_shipment', 'shipment_id'),
        Index('idx_shipment_item_material', 'material_id'),
        Index('idx_shipment_item_barcode', 'barcode_value'),
        Index('idx_shipment_item_package', 'package_id'),
        CheckConstraint('quantity > 0', name='chk_shipment_item_quantity_positive'),
        CheckConstraint('line_number > 0', name='chk_line_number_positive'),
    )

    def generate_barcode(self, barcode_type: BarcodeType = BarcodeType.CODE128, prefix: str = "SHIP") -> str:
        """
        Generate a barcode value for this shipment item.

        Args:
            barcode_type: Type of barcode to generate
            prefix: Prefix for the barcode value

        Returns:
            Generated barcode value (format: PREFIX-SHIPMENT_ID-LINE_NUMBER-TIMESTAMP)
        """
        import time
        timestamp = int(time.time())
        barcode_value = f"{prefix}-{self.shipment_id}-{self.line_number}-{timestamp}"
        self.barcode_value = barcode_value
        self.barcode_type = barcode_type
        return barcode_value

    def __repr__(self):
        return f"<ShipmentItem(shipment_id={self.shipment_id}, line={self.line_number}, qty={self.quantity})>"


class BarcodeLabel(Base):
    """
    Barcode Label entity - generated barcode/QR code labels.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Stores generated label metadata and file references.
    Can be linked to shipment items, materials, or other entities.
    """
    __tablename__ = "barcode_label"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)

    # Label identification
    label_code = Column(String(100), nullable=False, index=True)
    barcode_value = Column(String(100), nullable=False, index=True)
    barcode_type = Column(Enum(BarcodeType), nullable=False)

    # Entity reference (polymorphic)
    entity_type = Column(String(50), nullable=False)  # 'shipment_item', 'material', 'work_order', etc.
    entity_id = Column(Integer, nullable=False)

    # Specific relationship to shipment item (most common case)
    shipment_item_id = Column(Integer, ForeignKey('shipment_item.id', ondelete='CASCADE'), nullable=True, index=True)

    # Label format
    label_format = Column(String(50), nullable=False, default="PDF")  # PDF, PNG, ZPL, etc.
    label_size = Column(String(20), nullable=False, default="4x6")  # 4x6, 2x3, etc.

    # File storage
    file_path = Column(String(500), nullable=True)  # S3 path or local path
    file_url = Column(String(500), nullable=True)  # Public URL if applicable

    # Label content metadata
    label_data = Column(Text, nullable=True)  # JSON blob with additional label data

    # Print tracking
    print_count = Column(Integer, nullable=False, default=0)
    last_printed_at = Column(DateTime(timezone=True), nullable=True)
    printed_by_user_id = Column(Integer, nullable=True)

    # Validity
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Audit
    created_by_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shipment_item = relationship("ShipmentItem", back_populates="labels")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id', 'label_code',
                         name='uq_label_code_per_plant'),
        Index('idx_barcode_label_org_plant', 'organization_id', 'plant_id'),
        Index('idx_barcode_label_value', 'barcode_value'),
        Index('idx_barcode_label_entity', 'entity_type', 'entity_id'),
        Index('idx_barcode_label_shipment_item', 'shipment_item_id'),
        CheckConstraint('print_count >= 0', name='chk_print_count_non_negative'),
    )

    def generate_presigned_url(self, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for accessing the label file.

        Args:
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL string or None if no file_path

        Note:
            This is a placeholder implementation. In production, this would
            integrate with S3 or other cloud storage providers.
        """
        if not self.file_path:
            return None

        # Placeholder - would integrate with boto3 for S3
        # Example: s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=expiration)

        # For now, return a mock URL
        import time
        expiry_timestamp = int(time.time()) + expiration
        return f"{self.file_url}?expires={expiry_timestamp}" if self.file_url else None

    def __repr__(self):
        return f"<BarcodeLabel(code='{self.label_code}', type='{self.barcode_type}', entity={self.entity_type}:{self.entity_id})>"


class QRCodeScan(Base):
    """
    QR Code Scan entity - tracks scan events for barcodes/QR codes.

    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Designed as TimescaleDB hypertable for time-series scan data.
    Immutable audit trail of all scan events.
    Links to users, devices, and scanned entities.
    """
    __tablename__ = "qr_code_scan"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)

    # Scan identification
    scan_code = Column(String(100), nullable=False, index=True)  # Scanned barcode/QR value
    barcode_type = Column(Enum(BarcodeType), nullable=True)

    # Scan metadata
    scan_timestamp = Column(DateTime(timezone=True), nullable=False, index=True, server_default=func.now())
    scan_location = Column(String(200), nullable=True)  # Physical location or GPS coordinates
    device_id = Column(String(100), nullable=True, index=True)  # Scanner device identifier

    # Resolution (what entity was identified)
    scan_resolution = Column(Enum(ScanResolution), nullable=False, default=ScanResolution.SUCCESS, index=True)
    entity_type = Column(String(50), nullable=True)  # 'shipment', 'material', 'work_order', etc.
    entity_id = Column(Integer, nullable=True)

    # Context
    operation_context = Column(String(100), nullable=True)  # 'receiving', 'shipping', 'inventory_count', etc.
    work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='SET NULL'), nullable=True, index=True)
    shipment_id = Column(Integer, ForeignKey('shipment.id', ondelete='SET NULL'), nullable=True, index=True)

    # Additional data
    scan_data = Column(Text, nullable=True)  # JSON blob with additional scan metadata
    error_message = Column(Text, nullable=True)  # Error details if scan_resolution is ERROR

    # User tracking
    scanned_by_user_id = Column(Integer, nullable=False, index=True)

    # Immutable - no updated_at field
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    work_order = relationship("WorkOrder")
    shipment = relationship("Shipment")

    # Indexes for time-series queries
    # Note: In production, this would be converted to a TimescaleDB hypertable
    # using: SELECT create_hypertable('qr_code_scan', 'scan_timestamp');
    __table_args__ = (
        Index('idx_qr_scan_org_plant', 'organization_id', 'plant_id'),
        Index('idx_qr_scan_timestamp', 'scan_timestamp'),
        Index('idx_qr_scan_code', 'scan_code'),
        Index('idx_qr_scan_device', 'device_id'),
        Index('idx_qr_scan_resolution', 'scan_resolution'),
        Index('idx_qr_scan_entity', 'entity_type', 'entity_id'),
        Index('idx_qr_scan_user', 'scanned_by_user_id'),
        Index('idx_qr_scan_timestamp_org', 'scan_timestamp', 'organization_id', 'plant_id'),  # Time-series optimization
    )

    def resolve_entity(self) -> Optional[dict]:
        """
        Resolve the scanned entity and return its details.

        Returns:
            Dictionary with entity details or None if not resolved

        Example:
            {
                'entity_type': 'shipment_item',
                'entity_id': 123,
                'entity_data': {...}
            }
        """
        if self.scan_resolution != ScanResolution.SUCCESS or not self.entity_type or not self.entity_id:
            return None

        return {
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'scan_code': self.scan_code,
            'scan_timestamp': self.scan_timestamp,
            'operation_context': self.operation_context,
        }

    def __repr__(self):
        return f"<QRCodeScan(code='{self.scan_code}', resolution='{self.scan_resolution}', time={self.scan_timestamp})>"
