"""
LogisticsRepository - Infrastructure layer repositories for Logistics entities.

Provides repositories for:
- ShipmentRepository: Shipment CRUD and status transitions
- ShipmentItemRepository: Shipment item management and packing
- BarcodeLabelRepository: Barcode label generation and tracking
- QRCodeScanRepository: QR code scan recording and analytics

All repositories are RLS-aware with automatic context from database session.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, func, and_
from datetime import datetime, date, timedelta
import logging

from app.models.logistics import Shipment, ShipmentItem, BarcodeLabel, QRCodeScan

logger = logging.getLogger(__name__)


class ShipmentRepository:
    """
    Repository for Shipment entity persistence.

    Provides CRUD operations, status transitions, and search functionality.
    RLS context is automatically applied from database session.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session with RLS context
        """
        self._db = db

    def create(self, shipment_data: dict) -> Any:
        """
        Create new shipment.

        Args:
            shipment_data: Dictionary with shipment attributes

        Returns:
            Created Shipment entity

        Raises:
            ValueError: If validation fails or shipment number exists
        """
        db_shipment = Shipment(
            organization_id=shipment_data["organization_id"],
            plant_id=shipment_data["plant_id"],
            shipment_number=shipment_data["shipment_number"],
            shipment_type=shipment_data["shipment_type"],
            status=shipment_data.get("status", "draft"),
            customer_name=shipment_data.get("customer_name"),
            customer_code=shipment_data.get("customer_code"),
            vendor_name=shipment_data.get("vendor_name"),
            vendor_code=shipment_data.get("vendor_code"),
            destination_plant_id=shipment_data.get("destination_plant_id"),
            carrier_name=shipment_data.get("carrier_name"),
            tracking_number=shipment_data.get("tracking_number"),
            shipping_method=shipment_data.get("shipping_method"),
            shipping_address=shipment_data.get("shipping_address"),
            delivery_address=shipment_data.get("delivery_address"),
            planned_ship_date=shipment_data.get("planned_ship_date"),
            planned_delivery_date=shipment_data.get("planned_delivery_date"),
            total_packages=shipment_data.get("total_packages"),
            total_weight=shipment_data.get("total_weight"),
            weight_uom=shipment_data.get("weight_uom"),
            total_volume=shipment_data.get("total_volume"),
            volume_uom=shipment_data.get("volume_uom"),
            notes=shipment_data.get("notes"),
            special_instructions=shipment_data.get("special_instructions"),
            metadata=shipment_data.get("metadata"),
            created_by=shipment_data["created_by"],
        )

        try:
            self._db.add(db_shipment)
            self._db.commit()
            self._db.refresh(db_shipment)
            logger.info(f"Created shipment: {db_shipment.shipment_number}")
            return db_shipment
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to create shipment: {e}")
            raise ValueError(f"Shipment number {shipment_data['shipment_number']} already exists")

    def get_by_id(self, shipment_id: int) -> Optional[Any]:
        """
        Retrieve shipment by ID with items.

        Args:
            shipment_id: Shipment ID

        Returns:
            Shipment entity or None if not found
        """
        return (
            self._db.query(Shipment)
            .options(joinedload(Shipment.items))
            .filter(Shipment.id == shipment_id)
            .first()
        )

    def get_by_number(
        self, org_id: int, plant_id: int, shipment_number: str
    ) -> Optional[Any]:
        """
        Retrieve shipment by unique shipment_number within org/plant.

        Args:
            org_id: Organization ID
            plant_id: Plant ID
            shipment_number: Shipment number (unique)

        Returns:
            Shipment entity or None if not found
        """
        return (
            self._db.query(Shipment)
            .filter(Shipment.organization_id == org_id)
            .filter(Shipment.plant_id == plant_id)
            .filter(Shipment.shipment_number == shipment_number)
            .first()
        )

    def list_by_organization(
        self,
        org_id: int,
        plant_id: Optional[int] = None,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        List shipments with pagination and filtering.

        Args:
            org_id: Organization ID
            plant_id: Optional plant ID filter
            filters: Optional filters (status, type, date_from, date_to, tracking_number)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with items, total, page, page_size, total_pages
        """
        query = self._db.query(Shipment).filter(Shipment.organization_id == org_id)

        if plant_id is not None:
            query = query.filter(Shipment.plant_id == plant_id)

        # Apply filters
        if filters:
            if "status" in filters:
                query = query.filter(Shipment.status == filters["status"])
            if "shipment_type" in filters:
                query = query.filter(Shipment.shipment_type == filters["shipment_type"])
            if "tracking_number" in filters:
                query = query.filter(Shipment.tracking_number == filters["tracking_number"])
            if "date_from" in filters:
                query = query.filter(Shipment.planned_ship_date >= filters["date_from"])
            if "date_to" in filters:
                query = query.filter(Shipment.planned_ship_date <= filters["date_to"])

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_shipments_by_status(
        self,
        org_id: int,
        status: str,
        plant_id: Optional[int] = None,
    ) -> List[Any]:
        """
        Get shipments by status.

        Args:
            org_id: Organization ID
            status: Shipment status
            plant_id: Optional plant ID filter

        Returns:
            List of Shipment entities
        """
        query = (
            self._db.query(Shipment)
            .filter(Shipment.organization_id == org_id)
            .filter(Shipment.status == status)
        )

        if plant_id is not None:
            query = query.filter(Shipment.plant_id == plant_id)

        return query.all()

    def get_overdue_shipments(
        self,
        org_id: int,
        plant_id: Optional[int] = None,
    ) -> List[Any]:
        """
        Get shipments that are overdue (planned_ship_date in past, not yet shipped).

        Args:
            org_id: Organization ID
            plant_id: Optional plant ID filter

        Returns:
            List of overdue Shipment entities
        """
        today = date.today()

        query = (
            self._db.query(Shipment)
            .filter(Shipment.organization_id == org_id)
            .filter(Shipment.status.in_(["draft", "packed"]))
            .filter(Shipment.planned_ship_date < today)
            .filter(Shipment.actual_ship_date.is_(None))
        )

        if plant_id is not None:
            query = query.filter(Shipment.plant_id == plant_id)

        return query.all()

    def update(self, shipment_id: int, updates: dict) -> Any:
        """
        Update shipment.

        Args:
            shipment_id: Shipment ID to update
            updates: Dictionary with fields to update

        Returns:
            Updated Shipment entity

        Raises:
            ValueError: If shipment not found
        """
        db_shipment = self._db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not db_shipment:
            raise ValueError(f"Shipment with id {shipment_id} not found")

        # Update allowed fields
        updatable_fields = [
            "customer_name",
            "customer_code",
            "vendor_name",
            "vendor_code",
            "destination_plant_id",
            "carrier_name",
            "tracking_number",
            "shipping_method",
            "shipping_address",
            "delivery_address",
            "planned_ship_date",
            "planned_delivery_date",
            "total_packages",
            "total_weight",
            "weight_uom",
            "total_volume",
            "volume_uom",
            "notes",
            "special_instructions",
            "metadata",
        ]

        for field, value in updates.items():
            if field in updatable_fields:
                setattr(db_shipment, field, value)

        db_shipment.updated_at = datetime.utcnow()
        self._db.commit()
        self._db.refresh(db_shipment)
        logger.info(f"Updated shipment: {db_shipment.shipment_number}")
        return db_shipment

    def pack_shipment(self, shipment_id: int, packed_by_user_id: int) -> Any:
        """
        Mark shipment as packed.

        Args:
            shipment_id: Shipment ID
            packed_by_user_id: User ID who packed the shipment

        Returns:
            Updated Shipment entity

        Raises:
            ValueError: If shipment not found or invalid status
        """

        db_shipment = self._db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not db_shipment:
            raise ValueError(f"Shipment with id {shipment_id} not found")

        if db_shipment.status not in ["draft"]:
            raise ValueError(f"Cannot pack shipment with status {db_shipment.status}")

        db_shipment.status = "packed"
        db_shipment.packed_by = packed_by_user_id
        db_shipment.updated_at = datetime.utcnow()

        self._db.commit()
        self._db.refresh(db_shipment)
        logger.info(f"Packed shipment: {db_shipment.shipment_number}")
        return db_shipment

    def ship_shipment(
        self,
        shipment_id: int,
        shipped_by_user_id: int,
        tracking_number: Optional[str] = None,
    ) -> Any:
        """
        Mark shipment as shipped.

        Args:
            shipment_id: Shipment ID
            shipped_by_user_id: User ID who shipped the shipment
            tracking_number: Optional tracking number

        Returns:
            Updated Shipment entity

        Raises:
            ValueError: If shipment not found or invalid status
        """

        db_shipment = self._db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not db_shipment:
            raise ValueError(f"Shipment with id {shipment_id} not found")

        if db_shipment.status not in ["packed"]:
            raise ValueError(f"Cannot ship shipment with status {db_shipment.status}")

        db_shipment.status = "shipped"
        db_shipment.shipped_by = shipped_by_user_id
        db_shipment.actual_ship_date = datetime.utcnow()
        if tracking_number:
            db_shipment.tracking_number = tracking_number
        db_shipment.updated_at = datetime.utcnow()

        self._db.commit()
        self._db.refresh(db_shipment)
        logger.info(f"Shipped shipment: {db_shipment.shipment_number}")
        return db_shipment

    def deliver_shipment(self, shipment_id: int) -> Any:
        """
        Mark shipment as delivered.

        Args:
            shipment_id: Shipment ID

        Returns:
            Updated Shipment entity

        Raises:
            ValueError: If shipment not found or invalid status
        """

        db_shipment = self._db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not db_shipment:
            raise ValueError(f"Shipment with id {shipment_id} not found")

        if db_shipment.status not in ["shipped", "in_transit"]:
            raise ValueError(f"Cannot deliver shipment with status {db_shipment.status}")

        db_shipment.status = "delivered"
        db_shipment.actual_delivery_date = datetime.utcnow()
        db_shipment.updated_at = datetime.utcnow()

        self._db.commit()
        self._db.refresh(db_shipment)
        logger.info(f"Delivered shipment: {db_shipment.shipment_number}")
        return db_shipment

    def cancel_shipment(self, shipment_id: int) -> Any:
        """
        Cancel shipment.

        Args:
            shipment_id: Shipment ID

        Returns:
            Updated Shipment entity

        Raises:
            ValueError: If shipment not found or already delivered
        """
        db_shipment = self._db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not db_shipment:
            raise ValueError(f"Shipment with id {shipment_id} not found")

        if db_shipment.status == "delivered":
            raise ValueError("Cannot cancel a delivered shipment")

        db_shipment.status = "cancelled"
        db_shipment.updated_at = datetime.utcnow()

        self._db.commit()
        self._db.refresh(db_shipment)
        logger.info(f"Cancelled shipment: {db_shipment.shipment_number}")
        return db_shipment


class ShipmentItemRepository:
    """
    Repository for ShipmentItem entity persistence.

    Provides CRUD operations and packing operations.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session with RLS context
        """
        self._db = db

    def create(self, item_data: dict) -> Any:
        """
        Create new shipment item.

        Args:
            item_data: Dictionary with shipment item attributes

        Returns:
            Created ShipmentItem entity

        Raises:
            ValueError: If validation fails
        """
        db_item = ShipmentItem(
            organization_id=item_data["organization_id"],
            shipment_id=item_data["shipment_id"],
            line_number=item_data["line_number"],
            material_id=item_data.get("material_id"),
            work_order_id=item_data.get("work_order_id"),
            project_id=item_data.get("project_id"),
            item_description=item_data["item_description"],
            quantity=item_data["quantity"],
            uom=item_data["uom"],
            package_number=item_data.get("package_number"),
            package_type=item_data.get("package_type"),
            package_weight=item_data.get("package_weight"),
            package_dimensions=item_data.get("package_dimensions"),
            lot_number=item_data.get("lot_number"),
            serial_numbers=item_data.get("serial_numbers"),
            barcode=item_data.get("barcode"),
            qr_code=item_data.get("qr_code"),
            metadata=item_data.get("metadata"),
        )

        try:
            self._db.add(db_item)
            self._db.commit()
            self._db.refresh(db_item)
            logger.info(f"Created shipment item {db_item.line_number} for shipment {db_item.shipment_id}")
            return db_item
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to create shipment item: {e}")
            raise ValueError(f"Shipment item with line number {item_data['line_number']} already exists")

    def get_by_id(self, item_id: int) -> Optional[Any]:
        """
        Retrieve shipment item by ID.

        Args:
            item_id: ShipmentItem ID

        Returns:
            ShipmentItem entity or None if not found
        """
        return self._db.query(ShipmentItem).filter(ShipmentItem.id == item_id).first()

    def get_by_shipment(self, shipment_id: int) -> List[Any]:
        """
        Get all items for a shipment.

        Args:
            shipment_id: Shipment ID

        Returns:
            List of ShipmentItem entities
        """
        return (
            self._db.query(ShipmentItem)
            .filter(ShipmentItem.shipment_id == shipment_id)
            .order_by(ShipmentItem.line_number)
            .all()
        )

    def update(self, item_id: int, updates: dict) -> Any:
        """
        Update shipment item.

        Args:
            item_id: ShipmentItem ID
            updates: Dictionary with fields to update

        Returns:
            Updated ShipmentItem entity

        Raises:
            ValueError: If item not found
        """

        db_item = self._db.query(ShipmentItem).filter(ShipmentItem.id == item_id).first()
        if not db_item:
            raise ValueError(f"Shipment item with id {item_id} not found")

        # Update allowed fields
        updatable_fields = [
            "item_description",
            "quantity",
            "uom",
            "package_number",
            "package_type",
            "package_weight",
            "package_dimensions",
            "lot_number",
            "serial_numbers",
            "barcode",
            "qr_code",
            "metadata",
        ]

        for field, value in updates.items():
            if field in updatable_fields:
                setattr(db_item, field, value)

        db_item.updated_at = datetime.utcnow()
        self._db.commit()
        self._db.refresh(db_item)
        logger.info(f"Updated shipment item: {db_item.id}")
        return db_item

    def pack_item(self, item_id: int, packed_by_user_id: int) -> Any:
        """
        Mark shipment item as packed.

        Args:
            item_id: ShipmentItem ID
            packed_by_user_id: User ID who packed the item

        Returns:
            Updated ShipmentItem entity

        Raises:
            ValueError: If item not found
        """

        db_item = self._db.query(ShipmentItem).filter(ShipmentItem.id == item_id).first()
        if not db_item:
            raise ValueError(f"Shipment item with id {item_id} not found")

        db_item.is_packed = True
        db_item.packed_at = datetime.utcnow()
        db_item.packed_by = packed_by_user_id
        db_item.updated_at = datetime.utcnow()

        self._db.commit()
        self._db.refresh(db_item)
        logger.info(f"Packed shipment item: {db_item.id}")
        return db_item

    def delete(self, item_id: int) -> bool:
        """
        Delete shipment item.

        Args:
            item_id: ShipmentItem ID

        Returns:
            True if deleted, False if not found
        """
        db_item = self._db.query(ShipmentItem).filter(ShipmentItem.id == item_id).first()
        if not db_item:
            return False

        self._db.delete(db_item)
        self._db.commit()
        logger.info(f"Deleted shipment item: {item_id}")
        return True


class BarcodeLabelRepository:
    """
    Repository for BarcodeLabel entity persistence.

    Provides CRUD operations and generation tracking.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session with RLS context
        """
        self._db = db

    def create(self, label_data: dict) -> Any:
        """
        Create new barcode label record.

        Args:
            label_data: Dictionary with label attributes

        Returns:
            Created BarcodeLabel entity
        """
        db_label = BarcodeLabel(
            organization_id=label_data["organization_id"],
            plant_id=label_data["plant_id"],
            entity_type=label_data["entity_type"],
            entity_id=label_data["entity_id"],
            barcode_type=label_data["barcode_type"],
            barcode_value=label_data["barcode_value"],
            barcode_data=label_data.get("barcode_data"),
            label_format=label_data.get("label_format"),
            label_template=label_data.get("label_template"),
            file_path=label_data.get("file_path"),
            file_url=label_data.get("file_url"),
            metadata=label_data.get("metadata"),
            created_by=label_data.get("created_by"),
        )

        self._db.add(db_label)
        self._db.commit()
        self._db.refresh(db_label)
        logger.info(f"Created barcode label for {db_label.entity_type}/{db_label.entity_id}")
        return db_label

    def get_by_id(self, label_id: int) -> Optional[Any]:
        """
        Retrieve barcode label by ID.

        Args:
            label_id: BarcodeLabel ID

        Returns:
            BarcodeLabel entity or None if not found
        """
        return self._db.query(BarcodeLabel).filter(BarcodeLabel.id == label_id).first()

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        barcode_type: Optional[str] = None,
    ) -> List[Any]:
        """
        Get barcode labels for an entity.

        Args:
            entity_type: Entity type (material, work_order, shipment, package)
            entity_id: Entity ID
            barcode_type: Optional barcode type filter

        Returns:
            List of BarcodeLabel entities
        """
        query = (
            self._db.query(BarcodeLabel)
            .filter(BarcodeLabel.entity_type == entity_type)
            .filter(BarcodeLabel.entity_id == entity_id)
        )

        if barcode_type:
            query = query.filter(BarcodeLabel.barcode_type == barcode_type)

        return query.all()

    def get_by_value(self, barcode_value: str) -> Optional[Any]:
        """
        Get barcode label by barcode value.

        Args:
            barcode_value: Barcode value to search for

        Returns:
            BarcodeLabel entity or None if not found
        """
        return (
            self._db.query(BarcodeLabel)
            .filter(BarcodeLabel.barcode_value == barcode_value)
            .first()
        )

    def mark_generated(
        self,
        label_id: int,
        file_path: Optional[str] = None,
        file_url: Optional[str] = None,
    ) -> Any:
        """
        Mark label as generated.

        Args:
            label_id: BarcodeLabel ID
            file_path: Optional file path in storage
            file_url: Optional presigned URL

        Returns:
            Updated BarcodeLabel entity

        Raises:
            ValueError: If label not found
        """

        db_label = self._db.query(BarcodeLabel).filter(BarcodeLabel.id == label_id).first()
        if not db_label:
            raise ValueError(f"Barcode label with id {label_id} not found")

        db_label.is_generated = True
        db_label.generated_at = datetime.utcnow()
        if file_path:
            db_label.file_path = file_path
        if file_url:
            db_label.file_url = file_url
        db_label.updated_at = datetime.utcnow()

        self._db.commit()
        self._db.refresh(db_label)
        logger.info(f"Marked barcode label {label_id} as generated")
        return db_label

    def mark_printed(self, label_id: int, printed_by_user_id: int) -> Any:
        """
        Mark label as printed and increment print count.

        Args:
            label_id: BarcodeLabel ID
            printed_by_user_id: User ID who printed the label

        Returns:
            Updated BarcodeLabel entity

        Raises:
            ValueError: If label not found
        """

        db_label = self._db.query(BarcodeLabel).filter(BarcodeLabel.id == label_id).first()
        if not db_label:
            raise ValueError(f"Barcode label with id {label_id} not found")

        db_label.is_printed = True
        db_label.printed_at = datetime.utcnow()
        db_label.printed_by = printed_by_user_id
        db_label.print_count += 1
        db_label.updated_at = datetime.utcnow()

        self._db.commit()
        self._db.refresh(db_label)
        logger.info(f"Marked barcode label {label_id} as printed (count: {db_label.print_count})")
        return db_label

    def update(self, label_id: int, updates: dict) -> Any:
        """
        Update barcode label.

        Args:
            label_id: BarcodeLabel ID
            updates: Dictionary with fields to update

        Returns:
            Updated BarcodeLabel entity

        Raises:
            ValueError: If label not found
        """

        db_label = self._db.query(BarcodeLabel).filter(BarcodeLabel.id == label_id).first()
        if not db_label:
            raise ValueError(f"Barcode label with id {label_id} not found")

        updatable_fields = [
            "barcode_data",
            "label_format",
            "label_template",
            "file_path",
            "file_url",
            "metadata",
        ]

        for field, value in updates.items():
            if field in updatable_fields:
                setattr(db_label, field, value)

        db_label.updated_at = datetime.utcnow()
        self._db.commit()
        self._db.refresh(db_label)
        logger.info(f"Updated barcode label: {label_id}")
        return db_label


class QRCodeScanRepository:
    """
    Repository for QRCodeScan entity persistence.

    Provides scan recording and analytics for time-series data.
    Uses TimescaleDB hypertable for efficient time-based queries.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session with RLS context
        """
        self._db = db

    def create(self, scan_data: dict) -> Any:
        """
        Record a new QR code scan.

        Args:
            scan_data: Dictionary with scan attributes

        Returns:
            Created QRCodeScan entity
        """
        db_scan = QRCodeScan(
            organization_id=scan_data["organization_id"],
            plant_id=scan_data["plant_id"],
            scanned_by=scan_data["scanned_by"],
            scan_type=scan_data["scan_type"],
            scan_value=scan_data["scan_value"],
            entity_type=scan_data.get("entity_type"),
            entity_id=scan_data.get("entity_id"),
            resolution_status=scan_data.get("resolution_status", "not_found"),
            operation_type=scan_data.get("operation_type"),
            location=scan_data.get("location"),
            device_id=scan_data.get("device_id"),
            device_type=scan_data.get("device_type"),
            latitude=scan_data.get("latitude"),
            longitude=scan_data.get("longitude"),
            metadata=scan_data.get("metadata"),
        )

        self._db.add(db_scan)
        self._db.commit()
        self._db.refresh(db_scan)
        logger.info(f"Recorded scan: {db_scan.scan_value} by user {db_scan.scanned_by}")
        return db_scan

    def get_by_id(self, scan_id: int) -> Optional[Any]:
        """
        Retrieve scan by ID.

        Args:
            scan_id: QRCodeScan ID

        Returns:
            QRCodeScan entity or None if not found
        """
        return self._db.query(QRCodeScan).filter(QRCodeScan.id == scan_id).first()

    def get_scan_history(
        self,
        org_id: int,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        Get scan history with time-based filtering.

        Args:
            org_id: Organization ID
            filters: Optional filters (user_id, entity_type, entity_id, start_time, end_time)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with items, total, page, page_size, total_pages
        """
        query = self._db.query(QRCodeScan).filter(QRCodeScan.organization_id == org_id)

        # Apply filters
        if filters:
            if "user_id" in filters:
                query = query.filter(QRCodeScan.scanned_by == filters["user_id"])
            if "entity_type" in filters:
                query = query.filter(QRCodeScan.entity_type == filters["entity_type"])
            if "entity_id" in filters:
                query = query.filter(QRCodeScan.entity_id == filters["entity_id"])
            if "start_time" in filters:
                query = query.filter(QRCodeScan.scanned_at >= filters["start_time"])
            if "end_time" in filters:
                query = query.filter(QRCodeScan.scanned_at <= filters["end_time"])
            if "operation_type" in filters:
                query = query.filter(QRCodeScan.operation_type == filters["operation_type"])
            if "resolution_status" in filters:
                query = query.filter(QRCodeScan.resolution_status == filters["resolution_status"])

        # Order by time descending (most recent first)
        query = query.order_by(QRCodeScan.scanned_at.desc())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_scans_by_user(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Any]:
        """
        Get scans by user within time range.

        Args:
            user_id: User ID
            start_time: Optional start time
            end_time: Optional end time

        Returns:
            List of QRCodeScan entities
        """
        query = self._db.query(QRCodeScan).filter(QRCodeScan.scanned_by == user_id)

        if start_time:
            query = query.filter(QRCodeScan.scanned_at >= start_time)
        if end_time:
            query = query.filter(QRCodeScan.scanned_at <= end_time)

        return query.order_by(QRCodeScan.scanned_at.desc()).all()

    def get_scans_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Any]:
        """
        Get scans for a specific entity within time range.

        Args:
            entity_type: Entity type
            entity_id: Entity ID
            start_time: Optional start time
            end_time: Optional end time

        Returns:
            List of QRCodeScan entities
        """
        query = (
            self._db.query(QRCodeScan)
            .filter(QRCodeScan.entity_type == entity_type)
            .filter(QRCodeScan.entity_id == entity_id)
        )

        if start_time:
            query = query.filter(QRCodeScan.scanned_at >= start_time)
        if end_time:
            query = query.filter(QRCodeScan.scanned_at <= end_time)

        return query.order_by(QRCodeScan.scanned_at.desc()).all()

    def get_scan_analytics(
        self,
        org_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """
        Get scan analytics for time period.

        Args:
            org_id: Organization ID
            start_time: Start time
            end_time: End time

        Returns:
            Dictionary with analytics:
            - total_scans: Total number of scans
            - resolved_scans: Number of successfully resolved scans
            - not_found_scans: Number of scans not resolved
            - scans_by_user: Dictionary of scan counts by user_id
            - scans_by_operation: Dictionary of scan counts by operation_type
            - scans_by_entity_type: Dictionary of scan counts by entity_type
        """
        base_query = (
            self._db.query(QRCodeScan)
            .filter(QRCodeScan.organization_id == org_id)
            .filter(QRCodeScan.scanned_at >= start_time)
            .filter(QRCodeScan.scanned_at <= end_time)
        )

        # Total scans
        total_scans = base_query.count()

        # Scans by resolution status
        resolved_scans = base_query.filter(QRCodeScan.resolution_status == "resolved").count()
        not_found_scans = base_query.filter(QRCodeScan.resolution_status == "not_found").count()

        # Scans by user
        scans_by_user = {}
        user_stats = (
            base_query.with_entities(
                QRCodeScan.scanned_by, func.count(QRCodeScan.id).label("count")
            )
            .group_by(QRCodeScan.scanned_by)
            .all()
        )
        for user_id, count in user_stats:
            scans_by_user[user_id] = count

        # Scans by operation type
        scans_by_operation = {}
        operation_stats = (
            base_query.filter(QRCodeScan.operation_type.isnot(None))
            .with_entities(
                QRCodeScan.operation_type, func.count(QRCodeScan.id).label("count")
            )
            .group_by(QRCodeScan.operation_type)
            .all()
        )
        for operation, count in operation_stats:
            scans_by_operation[operation] = count

        # Scans by entity type
        scans_by_entity_type = {}
        entity_stats = (
            base_query.filter(QRCodeScan.entity_type.isnot(None))
            .with_entities(
                QRCodeScan.entity_type, func.count(QRCodeScan.id).label("count")
            )
            .group_by(QRCodeScan.entity_type)
            .all()
        )
        for entity_type, count in entity_stats:
            scans_by_entity_type[entity_type] = count

        return {
            "total_scans": total_scans,
            "resolved_scans": resolved_scans,
            "not_found_scans": not_found_scans,
            "scans_by_user": scans_by_user,
            "scans_by_operation": scans_by_operation,
            "scans_by_entity_type": scans_by_entity_type,
        }
