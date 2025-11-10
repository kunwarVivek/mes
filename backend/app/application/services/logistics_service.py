"""
LogisticsService - Application layer service for logistics operations.

Orchestrates logistics business logic for:
- Shipment lifecycle management (draft -> packed -> shipped -> delivered)
- Shipment item management and packing operations
- Barcode/QR code generation for shipments and items
- Scan processing and entity resolution
- Analytics and reporting

Integrates with:
- LogisticsRepository: Database operations
- BarcodeGenerationService: Code generation
- PGMQ: Async barcode generation
- MinIO: Label storage
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import json
import logging

from app.infrastructure.repositories.logistics_repository import (
    ShipmentRepository,
    ShipmentItemRepository,
    BarcodeLabelRepository,
    QRCodeScanRepository,
)
from app.infrastructure.messaging.pgmq_tasks import get_pgmq_client

logger = logging.getLogger(__name__)


class LogisticsService:
    """
    Application service for logistics operations.

    Coordinates shipment lifecycle, barcode generation, and scan tracking.
    """

    def __init__(
        self,
        shipment_repo: ShipmentRepository,
        shipment_item_repo: ShipmentItemRepository,
        barcode_label_repo: BarcodeLabelRepository,
        scan_repo: QRCodeScanRepository,
        barcode_generation_service: Optional[Any] = None,
    ):
        """
        Initialize LogisticsService.

        Args:
            shipment_repo: ShipmentRepository instance
            shipment_item_repo: ShipmentItemRepository instance
            barcode_label_repo: BarcodeLabelRepository instance
            scan_repo: QRCodeScanRepository instance
            barcode_generation_service: Optional BarcodeGenerationService
        """
        self._shipment_repo = shipment_repo
        self._item_repo = shipment_item_repo
        self._label_repo = barcode_label_repo
        self._scan_repo = scan_repo
        self._barcode_service = barcode_generation_service

    # ==================== Shipment Operations ====================

    def create_shipment(
        self,
        org_id: int,
        plant_id: int,
        shipment_number: str,
        shipment_type: str,
        created_by_user_id: int,
        items: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create new shipment with optional items.

        Args:
            org_id: Organization ID
            plant_id: Plant ID
            shipment_number: Unique shipment number
            shipment_type: Type (outbound, inbound, inter_plant)
            created_by_user_id: User creating the shipment
            items: Optional list of item dictionaries
            **kwargs: Additional shipment attributes

        Returns:
            Dictionary with shipment details

        Raises:
            ValueError: If validation fails
        """
        logger.info(f"Creating shipment {shipment_number} (type: {shipment_type})")

        # Validate shipment type
        valid_types = ["outbound", "inbound", "inter_plant"]
        if shipment_type not in valid_types:
            raise ValueError(f"Invalid shipment type: {shipment_type}. Must be one of {valid_types}")

        # Build shipment data
        shipment_data = {
            "organization_id": org_id,
            "plant_id": plant_id,
            "shipment_number": shipment_number,
            "shipment_type": shipment_type,
            "status": "draft",
            "created_by": created_by_user_id,
            **kwargs,
        }

        # Create shipment
        shipment = self._shipment_repo.create(shipment_data)

        # Add items if provided
        if items:
            for idx, item_data in enumerate(items, start=1):
                item_data["organization_id"] = org_id
                item_data["shipment_id"] = shipment.id
                item_data["line_number"] = item_data.get("line_number", idx)
                self._item_repo.create(item_data)

        logger.info(f"Created shipment {shipment_number} with {len(items) if items else 0} items")

        return self._shipment_to_dict(shipment)

    def get_shipment(self, shipment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get shipment by ID with items.

        Args:
            shipment_id: Shipment ID

        Returns:
            Shipment dictionary or None if not found
        """
        shipment = self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
            return None

        return self._shipment_to_dict(shipment)

    def update_shipment(
        self,
        shipment_id: int,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update shipment details.

        Args:
            shipment_id: Shipment ID
            updates: Dictionary with fields to update

        Returns:
            Updated shipment dictionary

        Raises:
            ValueError: If shipment not found
        """
        logger.info(f"Updating shipment {shipment_id}")
        shipment = self._shipment_repo.update(shipment_id, updates)
        return self._shipment_to_dict(shipment)

    def add_shipment_items(
        self,
        shipment_id: int,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Add items to existing shipment.

        Args:
            shipment_id: Shipment ID
            items: List of item dictionaries

        Returns:
            List of created item dictionaries

        Raises:
            ValueError: If shipment not found or not in draft status
        """
        logger.info(f"Adding {len(items)} items to shipment {shipment_id}")

        # Verify shipment exists and is in draft status
        shipment = self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise ValueError(f"Shipment {shipment_id} not found")

        if shipment.status not in ["draft"]:
            raise ValueError(f"Cannot add items to shipment with status {shipment.status}")

        # Get existing items to determine next line number
        existing_items = self._item_repo.get_by_shipment(shipment_id)
        next_line_number = max([item.line_number for item in existing_items], default=0) + 1

        created_items = []
        for item_data in items:
            item_data["organization_id"] = shipment.organization_id
            item_data["shipment_id"] = shipment_id
            item_data["line_number"] = item_data.get("line_number", next_line_number)
            next_line_number += 1

            item = self._item_repo.create(item_data)
            created_items.append(self._item_to_dict(item))

        logger.info(f"Added {len(created_items)} items to shipment {shipment_id}")
        return created_items

    def pack_shipment(
        self,
        shipment_id: int,
        packed_by_user_id: int,
    ) -> Dict[str, Any]:
        """
        Mark shipment as packed.

        Args:
            shipment_id: Shipment ID
            packed_by_user_id: User ID who packed the shipment

        Returns:
            Updated shipment dictionary

        Raises:
            ValueError: If shipment not found or invalid status
        """
        logger.info(f"Packing shipment {shipment_id}")

        shipment = self._shipment_repo.pack_shipment(shipment_id, packed_by_user_id)

        logger.info(f"Shipment {shipment_id} marked as packed")
        return self._shipment_to_dict(shipment)

    def ship_shipment(
        self,
        shipment_id: int,
        shipped_by_user_id: int,
        tracking_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ship shipment with optional tracking number.

        Args:
            shipment_id: Shipment ID
            shipped_by_user_id: User ID who shipped the shipment
            tracking_number: Optional carrier tracking number

        Returns:
            Updated shipment dictionary

        Raises:
            ValueError: If shipment not found or invalid status
        """
        logger.info(f"Shipping shipment {shipment_id}")

        shipment = self._shipment_repo.ship_shipment(
            shipment_id, shipped_by_user_id, tracking_number
        )

        logger.info(f"Shipment {shipment_id} marked as shipped (tracking: {tracking_number})")
        return self._shipment_to_dict(shipment)

    def deliver_shipment(self, shipment_id: int) -> Dict[str, Any]:
        """
        Mark shipment as delivered.

        Args:
            shipment_id: Shipment ID

        Returns:
            Updated shipment dictionary

        Raises:
            ValueError: If shipment not found or invalid status
        """
        logger.info(f"Delivering shipment {shipment_id}")

        shipment = self._shipment_repo.deliver_shipment(shipment_id)

        logger.info(f"Shipment {shipment_id} marked as delivered")
        return self._shipment_to_dict(shipment)

    def cancel_shipment(self, shipment_id: int) -> Dict[str, Any]:
        """
        Cancel shipment.

        Args:
            shipment_id: Shipment ID

        Returns:
            Updated shipment dictionary

        Raises:
            ValueError: If shipment not found or already delivered
        """
        logger.info(f"Cancelling shipment {shipment_id}")

        shipment = self._shipment_repo.cancel_shipment(shipment_id)

        logger.info(f"Shipment {shipment_id} cancelled")
        return self._shipment_to_dict(shipment)

    def get_shipments_by_status(
        self,
        org_id: int,
        status: str,
        plant_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get shipments by status.

        Args:
            org_id: Organization ID
            status: Shipment status
            plant_id: Optional plant ID filter

        Returns:
            List of shipment dictionaries
        """
        shipments = self._shipment_repo.get_shipments_by_status(org_id, status, plant_id)
        return [self._shipment_to_dict(s) for s in shipments]

    def get_overdue_shipments(
        self,
        org_id: int,
        plant_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get overdue shipments (planned_ship_date in past, not yet shipped).

        Args:
            org_id: Organization ID
            plant_id: Optional plant ID filter

        Returns:
            List of overdue shipment dictionaries
        """
        shipments = self._shipment_repo.get_overdue_shipments(org_id, plant_id)
        return [self._shipment_to_dict(s) for s in shipments]

    def get_shipment_status(self, shipment_id: int) -> Dict[str, Any]:
        """
        Get complete shipment status with items and tracking.

        Args:
            shipment_id: Shipment ID

        Returns:
            Dictionary with shipment, items, and status details

        Raises:
            ValueError: If shipment not found
        """
        shipment = self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise ValueError(f"Shipment {shipment_id} not found")

        items = self._item_repo.get_by_shipment(shipment_id)

        # Calculate packing progress
        total_items = len(items)
        packed_items = sum(1 for item in items if item.is_packed)
        packing_progress = (packed_items / total_items * 100) if total_items > 0 else 0

        return {
            "shipment": self._shipment_to_dict(shipment),
            "items": [self._item_to_dict(item) for item in items],
            "status_summary": {
                "current_status": shipment.status,
                "total_items": total_items,
                "packed_items": packed_items,
                "packing_progress": round(packing_progress, 2),
                "tracking_number": shipment.tracking_number,
                "planned_ship_date": shipment.planned_ship_date.isoformat() if shipment.planned_ship_date else None,
                "actual_ship_date": shipment.actual_ship_date.isoformat() if shipment.actual_ship_date else None,
                "actual_delivery_date": shipment.actual_delivery_date.isoformat() if shipment.actual_delivery_date else None,
            },
        }

    # ==================== Barcode Operations ====================

    def generate_barcode_async(
        self,
        org_id: int,
        plant_id: int,
        entity_type: str,
        entity_id: int,
        barcode_type: str,
        barcode_value: str,
        created_by_user_id: int,
        label_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Queue barcode generation job using PGMQ.

        Args:
            org_id: Organization ID
            plant_id: Plant ID
            entity_type: Entity type (material, work_order, shipment, package)
            barcode_type: Barcode type (code128, qr_code, datamatrix)
            barcode_value: Value to encode
            created_by_user_id: User requesting generation
            label_format: Optional label format

        Returns:
            Dictionary with label record and job info
        """
        logger.info(f"Queueing barcode generation for {entity_type}/{entity_id}")

        # Create barcode label record
        label_data = {
            "organization_id": org_id,
            "plant_id": plant_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "barcode_type": barcode_type,
            "barcode_value": barcode_value,
            "label_format": label_format,
            "created_by": created_by_user_id,
        }

        label = self._label_repo.create(label_data)

        # Queue generation job
        pgmq_client = get_pgmq_client()
        message = {
            "task": "generate_barcode",
            "label_id": label.id,
            "org_id": org_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "barcode_type": barcode_type,
            "barcode_value": barcode_value,
        }

        msg_id = pgmq_client.enqueue("barcode_generation", message)

        logger.info(f"Queued barcode generation job {msg_id} for label {label.id}")

        return {
            "label_id": label.id,
            "job_id": msg_id,
            "status": "queued",
            "barcode_value": barcode_value,
        }

    def scan_barcode(
        self,
        org_id: int,
        plant_id: int,
        scanned_by_user_id: int,
        scan_type: str,
        scan_value: str,
        operation_type: Optional[str] = None,
        metadata: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process barcode/QR scan and resolve entity.

        Args:
            org_id: Organization ID
            plant_id: Plant ID
            scanned_by_user_id: User ID who scanned
            scan_type: Scan type (barcode, qr_code)
            scan_value: Scanned value
            operation_type: Optional operation (receiving, shipping, inventory, production)
            metadata: Optional metadata
            **kwargs: Additional scan attributes (location, device_id, etc.)

        Returns:
            Dictionary with scan details and resolved entity
        """
        logger.info(f"Processing scan: {scan_value} by user {scanned_by_user_id}")

        # Attempt to resolve entity from barcode value
        entity = self._resolve_barcode(scan_value)

        # Determine resolution status
        if entity:
            resolution_status = "resolved"
            entity_type = entity["entity_type"]
            entity_id = entity["entity_id"]
        else:
            resolution_status = "not_found"
            entity_type = None
            entity_id = None

        # Record scan
        scan_data = {
            "organization_id": org_id,
            "plant_id": plant_id,
            "scanned_by": scanned_by_user_id,
            "scan_type": scan_type,
            "scan_value": scan_value,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "resolution_status": resolution_status,
            "operation_type": operation_type,
            "metadata": metadata,
            **kwargs,
        }

        scan = self._scan_repo.create(scan_data)

        logger.info(
            f"Recorded scan {scan.id}: {resolution_status} "
            f"({entity_type}/{entity_id} if resolved else 'N/A'})"
        )

        return {
            "scan_id": scan.id,
            "scan_value": scan_value,
            "resolution_status": resolution_status,
            "entity": entity,
            "scanned_at": scan.scanned_at.isoformat(),
        }

    def lookup_barcode(self, barcode_value: str) -> Optional[Dict[str, Any]]:
        """
        Look up entity by barcode value.

        Args:
            barcode_value: Barcode value to search

        Returns:
            Entity dictionary or None if not found
        """
        return self._resolve_barcode(barcode_value)

    def get_scan_history(
        self,
        org_id: int,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Get scan history with filtering and pagination.

        Args:
            org_id: Organization ID
            filters: Optional filters (user_id, entity_type, entity_id, start_time, end_time)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated scan history
        """
        return self._scan_repo.get_scan_history(org_id, filters, page, page_size)

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
            Analytics dictionary with scan statistics
        """
        analytics = self._scan_repo.get_scan_analytics(org_id, start_time, end_time)

        # Add success rate
        total = analytics["total_scans"]
        resolved = analytics["resolved_scans"]
        analytics["success_rate"] = (resolved / total * 100) if total > 0 else 0

        return analytics

    # ==================== Helper Methods ====================

    def _resolve_barcode(self, barcode_value: str) -> Optional[Dict[str, Any]]:
        """
        Resolve barcode value to entity.

        Looks up barcode in barcode_labels table.

        Args:
            barcode_value: Barcode value to resolve

        Returns:
            Dictionary with entity_type and entity_id, or None if not found
        """
        label = self._label_repo.get_by_value(barcode_value)

        if not label:
            return None

        return {
            "entity_type": label.entity_type,
            "entity_id": label.entity_id,
            "barcode_type": label.barcode_type,
            "label_id": label.id,
        }

    def _shipment_to_dict(self, shipment: Any) -> Dict[str, Any]:
        """Convert shipment entity to dictionary."""
        return {
            "id": shipment.id,
            "organization_id": shipment.organization_id,
            "plant_id": shipment.plant_id,
            "shipment_number": shipment.shipment_number,
            "shipment_type": shipment.shipment_type,
            "status": shipment.status,
            "customer_name": shipment.customer_name,
            "customer_code": shipment.customer_code,
            "vendor_name": shipment.vendor_name,
            "vendor_code": shipment.vendor_code,
            "destination_plant_id": shipment.destination_plant_id,
            "carrier_name": shipment.carrier_name,
            "tracking_number": shipment.tracking_number,
            "shipping_method": shipment.shipping_method,
            "shipping_address": shipment.shipping_address,
            "delivery_address": shipment.delivery_address,
            "planned_ship_date": shipment.planned_ship_date.isoformat() if shipment.planned_ship_date else None,
            "actual_ship_date": shipment.actual_ship_date.isoformat() if shipment.actual_ship_date else None,
            "planned_delivery_date": shipment.planned_delivery_date.isoformat() if shipment.planned_delivery_date else None,
            "actual_delivery_date": shipment.actual_delivery_date.isoformat() if shipment.actual_delivery_date else None,
            "total_packages": shipment.total_packages,
            "total_weight": shipment.total_weight,
            "weight_uom": shipment.weight_uom,
            "total_volume": shipment.total_volume,
            "volume_uom": shipment.volume_uom,
            "notes": shipment.notes,
            "special_instructions": shipment.special_instructions,
            "metadata": shipment.metadata,
            "created_at": shipment.created_at.isoformat(),
            "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None,
            "created_by": shipment.created_by,
            "packed_by": shipment.packed_by,
            "shipped_by": shipment.shipped_by,
        }

    def _item_to_dict(self, item: Any) -> Dict[str, Any]:
        """Convert shipment item entity to dictionary."""
        return {
            "id": item.id,
            "organization_id": item.organization_id,
            "shipment_id": item.shipment_id,
            "line_number": item.line_number,
            "material_id": item.material_id,
            "work_order_id": item.work_order_id,
            "project_id": item.project_id,
            "item_description": item.item_description,
            "quantity": item.quantity,
            "uom": item.uom,
            "package_number": item.package_number,
            "package_type": item.package_type,
            "package_weight": item.package_weight,
            "package_dimensions": item.package_dimensions,
            "lot_number": item.lot_number,
            "serial_numbers": item.serial_numbers,
            "barcode": item.barcode,
            "qr_code": item.qr_code,
            "is_packed": item.is_packed,
            "packed_at": item.packed_at.isoformat() if item.packed_at else None,
            "packed_by": item.packed_by,
            "metadata": item.metadata,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
