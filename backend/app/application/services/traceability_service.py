"""
Traceability Service - Business logic for lot/serial tracking and genealogy
"""
from typing import List, Optional, Dict, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timezone
from decimal import Decimal
import logging

from app.models.traceability import (
    LotBatch,
    SerialNumber,
    TraceabilityLink,
    GenealogyRecord
)
from app.models.work_order import WorkOrder
from app.models.material import Material
from app.models.logistics import Shipment, ShipmentItem
from app.infrastructure.repositories.traceability_repository import (
    LotBatchRepository,
    SerialNumberRepository,
    TraceabilityLinkRepository,
    GenealogyRecordRepository,
)
from app.application.dtos.traceability_dto import (
    LotBatchCreateDTO,
    LotBatchUpdateDTO,
    LotBatchReserveDTO,
    LotBatchConsumeDTO,
    SerialNumberCreateDTO,
    SerialNumberUpdateDTO,
    SerialNumberShipDTO,
    TraceabilityLinkCreateDTO,
    GenealogyRecordCreateDTO,
    GenealogyQueryRequest,
    WhereUsedRequest,
    WhereFromRequest,
    GenealogyTreeNode,
    GenealogyTreeResponse,
    RecallReportRequest,
    RecallReportResponse,
    AffectedWorkOrderDTO,
    AffectedShipmentDTO,
    AffectedCustomerDTO,
    DownstreamImpactDTO,
)

logger = logging.getLogger(__name__)


class LotBatchService:
    """Service for Lot Batch operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = LotBatchRepository(db)
        self.genealogy_repo = GenealogyRecordRepository(db)

    def create_lot(self, dto: LotBatchCreateDTO) -> LotBatch:
        """Create a new lot batch and record in genealogy"""
        # Check for duplicate lot number
        existing = self.repo.get_by_lot_number(dto.organization_id, dto.lot_number)
        if existing:
            raise ValueError(f"Lot number '{dto.lot_number}' already exists")

        lot = self.repo.create(dto)

        # Record in genealogy
        genealogy_dto = GenealogyRecordCreateDTO(
            organization_id=lot.organization_id,
            entity_type='LOT',
            entity_id=lot.id,
            entity_identifier=lot.lot_number,
            operation_type='CREATED',
            operation_timestamp=lot.created_at,
            quantity_after=lot.initial_quantity,
            status_after=lot.quality_status,
            location_after=lot.warehouse_location,
            metadata={"source_type": lot.source_type},
            performed_by=lot.created_by,
        )
        self.genealogy_repo.create(genealogy_dto)

        return lot

    def get_lot(self, lot_id: int) -> Optional[LotBatch]:
        """Get lot batch by ID"""
        return self.repo.get_by_id(lot_id)

    def get_by_lot_number(self, organization_id: int, lot_number: str) -> Optional[LotBatch]:
        """Get lot batch by lot number"""
        return self.repo.get_by_lot_number(organization_id, lot_number)

    def list_lots(self, organization_id: int, skip: int = 0, limit: int = 100,
                  material_id: Optional[int] = None, quality_status: Optional[str] = None,
                  active_only: bool = True) -> List[LotBatch]:
        """List lot batches"""
        return self.repo.list_by_organization(organization_id, skip, limit, material_id, quality_status, active_only)

    def list_by_material(self, material_id: int, quality_status: Optional[str] = None,
                        available_only: bool = False) -> List[LotBatch]:
        """List lot batches for a material"""
        return self.repo.list_by_material(material_id, quality_status, available_only)

    def list_expiring_soon(self, organization_id: int, days: int = 30) -> List[LotBatch]:
        """List lots expiring soon"""
        return self.repo.list_expiring_soon(organization_id, days)

    def list_needing_retest(self, organization_id: int) -> List[LotBatch]:
        """List lots needing retest"""
        return self.repo.list_needing_retest(organization_id)

    def update_lot(self, lot_id: int, dto: LotBatchUpdateDTO, updated_by: int) -> Optional[LotBatch]:
        """Update lot batch"""
        lot = self.repo.get_by_id(lot_id)
        if not lot:
            return None

        # Capture before state
        qty_before = lot.current_quantity
        status_before = lot.quality_status
        location_before = lot.warehouse_location

        # Update
        updated_lot = self.repo.update(lot_id, dto)

        # Record changes in genealogy if significant
        if (dto.quality_status and dto.quality_status != status_before):
            genealogy_dto = GenealogyRecordCreateDTO(
                organization_id=lot.organization_id,
                entity_type='LOT',
                entity_id=lot.id,
                entity_identifier=lot.lot_number,
                operation_type='INSPECTED' if dto.quality_status == 'RELEASED' else 'QUARANTINED',
                operation_timestamp=datetime.now(timezone.utc),
                status_before=status_before,
                status_after=dto.quality_status,
                performed_by=updated_by,
            )
            self.genealogy_repo.create(genealogy_dto)

        return updated_lot

    def reserve_quantity(self, lot_id: int, dto: LotBatchReserveDTO) -> LotBatch:
        """Reserve quantity from lot"""
        lot = self.repo.get_by_id(lot_id)
        if not lot:
            raise ValueError(f"Lot {lot_id} not found")

        if not lot.reserve_quantity(float(dto.quantity)):
            raise ValueError(f"Insufficient available quantity. Available: {lot.get_available_quantity()}")

        self.db.commit()
        self.db.refresh(lot)

        # Record in genealogy
        genealogy_dto = GenealogyRecordCreateDTO(
            organization_id=lot.organization_id,
            entity_type='LOT',
            entity_id=lot.id,
            entity_identifier=lot.lot_number,
            operation_type='RESERVED',
            operation_timestamp=datetime.now(timezone.utc),
            quantity_before=lot.current_quantity,
            quantity_after=lot.current_quantity,
            metadata={"reserved": float(dto.quantity), "reference_type": dto.reference_type, "reference_id": dto.reference_id},
            performed_by=dto.reserved_by,
        )
        self.genealogy_repo.create(genealogy_dto)

        return lot

    def consume_quantity(self, lot_id: int, dto: LotBatchConsumeDTO) -> LotBatch:
        """Consume quantity from lot"""
        lot = self.repo.get_by_id(lot_id)
        if not lot:
            raise ValueError(f"Lot {lot_id} not found")

        qty_before = lot.current_quantity

        if not lot.consume_quantity(float(dto.quantity)):
            raise ValueError(f"Insufficient quantity. Current: {lot.current_quantity}")

        self.db.commit()
        self.db.refresh(lot)

        # Record in genealogy
        genealogy_dto = GenealogyRecordCreateDTO(
            organization_id=lot.organization_id,
            entity_type='LOT',
            entity_id=lot.id,
            entity_identifier=lot.lot_number,
            operation_type='CONSUMED',
            operation_timestamp=datetime.now(timezone.utc),
            work_order_id=dto.work_order_id,
            quantity_before=qty_before,
            quantity_after=lot.current_quantity,
            quantity_change=-float(dto.quantity),
            metadata={"operation_sequence": dto.operation_sequence},
            performed_by=dto.consumed_by,
        )
        self.genealogy_repo.create(genealogy_dto)

        return lot

    def delete_lot(self, lot_id: int) -> bool:
        """Delete lot batch (soft delete)"""
        return self.repo.delete(lot_id)


class SerialNumberService:
    """Service for Serial Number operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = SerialNumberRepository(db)
        self.genealogy_repo = GenealogyRecordRepository(db)

    def create_serial(self, dto: SerialNumberCreateDTO) -> SerialNumber:
        """Create a new serial number and record in genealogy"""
        # Check for duplicate serial
        existing = self.repo.get_by_serial_number(dto.organization_id, dto.serial_number)
        if existing:
            raise ValueError(f"Serial number '{dto.serial_number}' already exists")

        serial = self.repo.create(dto)

        # Record in genealogy
        genealogy_dto = GenealogyRecordCreateDTO(
            organization_id=serial.organization_id,
            entity_type='SERIAL',
            entity_id=serial.id,
            entity_identifier=serial.serial_number,
            operation_type='CREATED',
            operation_timestamp=serial.created_at,
            work_order_id=serial.work_order_id,
            status_after=serial.status,
            location_after=serial.warehouse_location,
            metadata={"lot_batch_id": serial.lot_batch_id, "production_line": serial.production_line},
            performed_by=serial.created_by,
        )
        self.genealogy_repo.create(genealogy_dto)

        return serial

    def get_serial(self, serial_id: int) -> Optional[SerialNumber]:
        """Get serial number by ID"""
        return self.repo.get_by_id(serial_id)

    def get_by_serial_number(self, organization_id: int, serial_number: str) -> Optional[SerialNumber]:
        """Get serial number by serial"""
        return self.repo.get_by_serial_number(organization_id, serial_number)

    def list_serials(self, organization_id: int, skip: int = 0, limit: int = 100,
                    material_id: Optional[int] = None, status: Optional[str] = None,
                    customer_id: Optional[int] = None) -> List[SerialNumber]:
        """List serial numbers"""
        return self.repo.list_by_organization(organization_id, skip, limit, material_id, status, customer_id)

    def list_by_lot(self, lot_batch_id: int) -> List[SerialNumber]:
        """List serial numbers for a lot"""
        return self.repo.list_by_lot(lot_batch_id)

    def list_by_customer(self, customer_id: int, skip: int = 0, limit: int = 100) -> List[SerialNumber]:
        """List serial numbers for a customer"""
        return self.repo.list_by_customer(customer_id, skip, limit)

    def list_in_warranty(self, organization_id: int) -> List[SerialNumber]:
        """List serial numbers under warranty"""
        return self.repo.list_in_warranty(organization_id)

    def update_serial(self, serial_id: int, dto: SerialNumberUpdateDTO, updated_by: int) -> Optional[SerialNumber]:
        """Update serial number"""
        serial = self.repo.get_by_id(serial_id)
        if not serial:
            return None

        # Capture before state
        status_before = serial.status
        location_before = serial.current_location

        # Update
        updated_serial = self.repo.update(serial_id, dto)

        # Record significant changes in genealogy
        if dto.status and dto.status != status_before:
            operation_type = 'SHIPPED' if dto.status == 'SHIPPED' else 'LOCATION_CHANGED'
            if dto.status == 'INSTALLED':
                operation_type = 'INSTALLED'

            genealogy_dto = GenealogyRecordCreateDTO(
                organization_id=serial.organization_id,
                entity_type='SERIAL',
                entity_id=serial.id,
                entity_identifier=serial.serial_number,
                operation_type=operation_type,
                operation_timestamp=datetime.now(timezone.utc),
                status_before=status_before,
                status_after=dto.status,
                location_before=location_before,
                location_after=dto.current_location,
                metadata={"customer_id": dto.customer_id, "shipment_id": dto.shipment_id},
                performed_by=updated_by,
            )
            self.genealogy_repo.create(genealogy_dto)

        return updated_serial

    def ship_serial(self, serial_id: int, dto: SerialNumberShipDTO) -> SerialNumber:
        """Ship a serial number"""
        serial = self.repo.get_by_id(serial_id)
        if not serial:
            raise ValueError(f"Serial {serial_id} not found")

        if serial.status != 'IN_STOCK':
            raise ValueError(f"Serial must be IN_STOCK to ship. Current status: {serial.status}")

        # Update serial
        update_dto = SerialNumberUpdateDTO(
            status='SHIPPED',
            customer_id=dto.customer_id,
            shipment_id=dto.shipment_id,
            shipped_date=dto.shipped_date,
        )

        return self.update_serial(serial_id, update_dto, dto.shipped_by)

    def delete_serial(self, serial_id: int) -> bool:
        """Delete serial number (soft delete)"""
        return self.repo.delete(serial_id)


class TraceabilityLinkService:
    """Service for Traceability Link operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = TraceabilityLinkRepository(db)

    def create_link(self, dto: TraceabilityLinkCreateDTO) -> TraceabilityLink:
        """Create a new traceability link"""
        return self.repo.create(dto)

    def get_link(self, link_id: int) -> Optional[TraceabilityLink]:
        """Get traceability link by ID"""
        return self.repo.get_by_id(link_id)

    def list_by_parent_lot(self, parent_lot_id: int) -> List[TraceabilityLink]:
        """List links for parent lot"""
        return self.repo.list_by_parent_lot(parent_lot_id)

    def list_by_child_lot(self, child_lot_id: int) -> List[TraceabilityLink]:
        """List links for child lot"""
        return self.repo.list_by_child_lot(child_lot_id)

    def list_by_work_order(self, work_order_id: int) -> List[TraceabilityLink]:
        """List links for work order"""
        return self.repo.list_by_work_order(work_order_id)


class GenealogyService:
    """Service for Genealogy queries and tree building"""

    def __init__(self, db: Session):
        self.db = db
        self.genealogy_repo = GenealogyRecordRepository(db)
        self.link_repo = TraceabilityLinkRepository(db)
        self.lot_repo = LotBatchRepository(db)
        self.serial_repo = SerialNumberRepository(db)

    def query_history(self, request: GenealogyQueryRequest) -> List[GenealogyRecord]:
        """Query genealogy history for an entity"""
        return self.genealogy_repo.list_by_entity(
            request.entity_type,
            request.entity_identifier,
            request.start_date,
            request.end_date
        )

    def build_where_used_tree(self, request: WhereUsedRequest) -> GenealogyTreeResponse:
        """
        Build where-used tree (forward genealogy).
        Shows where this entity was used/consumed.
        """
        visited: Set[str] = set()
        root = self._build_where_used_node(request.entity_type, request.entity_id, 0, request.max_depth, visited)

        total_nodes = len(visited)
        max_depth = self._get_max_depth(root)

        return GenealogyTreeResponse(
            root=root,
            total_nodes=total_nodes,
            max_depth_reached=max_depth
        )

    def _build_where_used_node(self, entity_type: str, entity_id: int, current_depth: int,
                               max_depth: int, visited: Set[str]) -> GenealogyTreeNode:
        """Recursively build where-used tree node"""
        # Create unique key for visited tracking
        key = f"{entity_type}:{entity_id}"
        if key in visited or current_depth >= max_depth:
            # Return node without children to prevent infinite loops
            entity_identifier, material_id = self._get_entity_info(entity_type, entity_id)
            return GenealogyTreeNode(
                entity_type=entity_type,
                entity_id=entity_id,
                entity_identifier=entity_identifier,
                material_id=material_id,
                depth=current_depth,
                children=[]
            )

        visited.add(key)

        # Get entity info
        entity_identifier, material_id = self._get_entity_info(entity_type, entity_id)

        # Find children (entities that consumed/used this entity)
        children = []

        if entity_type == 'LOT':
            links = self.link_repo.list_by_parent_lot(entity_id)
        else:
            links = self.link_repo.list_by_parent_serial(entity_id)

        for link in links:
            child_type = link.child_type
            child_id = link.child_lot_id if child_type == 'LOT' else link.child_serial_id

            child_node = self._build_where_used_node(child_type, child_id, current_depth + 1, max_depth, visited)
            child_node.relationship_type = link.relationship_type
            child_node.quantity = link.quantity_used
            children.append(child_node)

        return GenealogyTreeNode(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_identifier=entity_identifier,
            material_id=material_id,
            depth=current_depth,
            children=children
        )

    def build_where_from_tree(self, request: WhereFromRequest) -> GenealogyTreeResponse:
        """
        Build where-from tree (reverse genealogy).
        Shows what components/materials went into this entity.
        """
        visited: Set[str] = set()
        root = self._build_where_from_node(request.entity_type, request.entity_id, 0, request.max_depth, visited)

        total_nodes = len(visited)
        max_depth = self._get_max_depth(root)

        return GenealogyTreeResponse(
            root=root,
            total_nodes=total_nodes,
            max_depth_reached=max_depth
        )

    def _build_where_from_node(self, entity_type: str, entity_id: int, current_depth: int,
                               max_depth: int, visited: Set[str]) -> GenealogyTreeNode:
        """Recursively build where-from tree node"""
        # Create unique key
        key = f"{entity_type}:{entity_id}"
        if key in visited or current_depth >= max_depth:
            entity_identifier, material_id = self._get_entity_info(entity_type, entity_id)
            return GenealogyTreeNode(
                entity_type=entity_type,
                entity_id=entity_id,
                entity_identifier=entity_identifier,
                material_id=material_id,
                depth=current_depth,
                children=[]
            )

        visited.add(key)

        # Get entity info
        entity_identifier, material_id = self._get_entity_info(entity_type, entity_id)

        # Find parents (entities that were consumed to create this entity)
        children = []

        if entity_type == 'LOT':
            links = self.link_repo.list_by_child_lot(entity_id)
        else:
            links = self.link_repo.list_by_child_serial(entity_id)

        for link in links:
            parent_type = link.parent_type
            parent_id = link.parent_lot_id if parent_type == 'LOT' else link.parent_serial_id

            parent_node = self._build_where_from_node(parent_type, parent_id, current_depth + 1, max_depth, visited)
            parent_node.relationship_type = link.relationship_type
            parent_node.quantity = link.quantity_used
            children.append(parent_node)

        return GenealogyTreeNode(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_identifier=entity_identifier,
            material_id=material_id,
            depth=current_depth,
            children=children
        )

    def _get_entity_info(self, entity_type: str, entity_id: int) -> tuple:
        """Get entity identifier and material_id"""
        if entity_type == 'LOT':
            entity = self.lot_repo.get_by_id(entity_id)
            if entity:
                return entity.lot_number, entity.material_id
        else:
            entity = self.serial_repo.get_by_id(entity_id)
            if entity:
                return entity.serial_number, entity.material_id

        return f"UNKNOWN_{entity_id}", None

    def _get_max_depth(self, node: GenealogyTreeNode) -> int:
        """Get maximum depth of tree"""
        if not node.children:
            return node.depth

        return max(self._get_max_depth(child) for child in node.children)


class RecallReportService:
    """Service for Recall Report generation"""

    def __init__(self, db: Session):
        self.db = db
        self.lot_repo = LotBatchRepository(db)
        self.link_repo = TraceabilityLinkRepository(db)
        self.serial_repo = SerialNumberRepository(db)

    def generate_recall_report(
        self,
        request: RecallReportRequest,
        user_id: int,
        organization_id: int
    ) -> RecallReportResponse:
        """
        Generate a comprehensive recall report for affected lots.

        Performs forward genealogy trace: Lot → Work Orders → Shipments → Customers

        Args:
            request: Recall report request with material_id, lot_numbers, reason, severity
            user_id: User ID generating the report
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            RecallReportResponse with complete traceability data

        Raises:
            ValueError: If material or lot numbers are invalid
        """
        logger.info(f"Generating recall report for material_id={request.material_id}, lots={request.lot_numbers}")

        # Step 1: Validate inputs
        material = self._validate_material(request.material_id, organization_id)
        lot_batches = self._validate_lots(request.lot_numbers, request.material_id, organization_id)

        # Step 2: Generate report ID
        report_id = self._generate_report_id()

        # Step 3: Calculate total quantity affected
        total_quantity_affected = sum(
            Decimal(str(lot.initial_quantity)) for lot in lot_batches
        )

        # Step 4: Forward Genealogy Trace - Find affected work orders
        affected_work_orders = self._trace_affected_work_orders(lot_batches)

        # Step 5: Find affected shipments and customers
        affected_shipments, affected_customers = self._trace_affected_shipments(
            lot_batches,
            affected_work_orders,
            request.include_customer_details
        )

        # Step 6: Build downstream impact summary
        downstream_impact = DownstreamImpactDTO(
            total_affected_work_orders=len(affected_work_orders),
            total_affected_shipments=len(affected_shipments),
            total_affected_customers=len(affected_customers),
            total_quantity_shipped=sum(s.quantity for s in affected_shipments)
        )

        # Step 7: Build and return report
        report = RecallReportResponse(
            report_id=report_id,
            material_id=material.id,
            material_number=material.material_number,
            material_description=material.description or material.material_name,
            affected_lots=request.lot_numbers,
            reason=request.reason,
            severity=request.severity,
            generated_at=datetime.now(timezone.utc),
            generated_by_user_id=user_id,
            total_quantity_affected=total_quantity_affected,
            affected_work_orders=affected_work_orders,
            affected_shipments=affected_shipments,
            affected_customers=affected_customers,
            downstream_impact=downstream_impact
        )

        logger.info(
            f"Recall report {report_id} generated: "
            f"{len(affected_work_orders)} WOs, "
            f"{len(affected_shipments)} shipments, "
            f"{len(affected_customers)} customers"
        )

        return report

    def _validate_material(self, material_id: int, organization_id: int) -> Material:
        """Validate material exists and belongs to organization"""
        material = self.db.query(Material).filter(
            and_(
                Material.id == material_id,
                Material.organization_id == organization_id
            )
        ).first()

        if not material:
            raise ValueError(f"Material {material_id} not found")

        return material

    def _validate_lots(
        self,
        lot_numbers: List[str],
        material_id: int,
        organization_id: int
    ) -> List[LotBatch]:
        """Validate all lot numbers exist and belong to the material"""
        lot_batches = []

        for lot_number in lot_numbers:
            lot = self.lot_repo.get_by_lot_number(organization_id, lot_number)

            if not lot:
                raise ValueError(f"Lot '{lot_number}' not found")

            if lot.material_id != material_id:
                raise ValueError(
                    f"Lot '{lot_number}' does not belong to material {material_id}"
                )

            lot_batches.append(lot)

        return lot_batches

    def _generate_report_id(self) -> str:
        """Generate unique report ID in format RECALL-YYYY-NNNN"""
        current_year = datetime.now(timezone.utc).year

        # Simple sequence generation - in production, use database sequence
        # For now, use timestamp-based unique ID
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000) % 10000

        return f"RECALL-{current_year}-{timestamp:04d}"

    def _trace_affected_work_orders(
        self,
        lot_batches: List[LotBatch]
    ) -> List[AffectedWorkOrderDTO]:
        """
        Trace which work orders consumed the affected lots.

        Uses traceability_links table to find work orders that consumed these lots.
        """
        lot_ids = [lot.id for lot in lot_batches]

        # Query traceability links to find work orders that consumed these lots
        # Parent lot = affected lot, Child = produced lot/serial
        links = self.db.query(TraceabilityLink).filter(
            and_(
                TraceabilityLink.parent_lot_id.in_(lot_ids),
                TraceabilityLink.work_order_id.isnot(None)
            )
        ).all()

        # Get unique work order IDs
        work_order_ids = list(set(link.work_order_id for link in links if link.work_order_id))

        if not work_order_ids:
            logger.info("No work orders found that consumed the affected lots")
            return []

        # Query work orders with details
        work_orders = self.db.query(WorkOrder).filter(
            WorkOrder.id.in_(work_order_ids)
        ).all()

        # Build affected work orders list
        affected_wos = []
        for wo in work_orders:
            # Calculate total quantity consumed from affected lots
            consumed_qty = sum(
                Decimal(str(link.quantity_used or 0))
                for link in links
                if link.work_order_id == wo.id
            )

            affected_wos.append(AffectedWorkOrderDTO(
                work_order_id=wo.id,
                work_order_number=wo.work_order_number,
                quantity_consumed=consumed_qty,
                status=wo.order_status.value if hasattr(wo.order_status, 'value') else str(wo.order_status),
                completion_date=wo.end_date_actual
            ))

        return affected_wos

    def _trace_affected_shipments(
        self,
        lot_batches: List[LotBatch],
        affected_work_orders: List[AffectedWorkOrderDTO],
        include_customer_details: bool
    ) -> tuple[List[AffectedShipmentDTO], List[AffectedCustomerDTO]]:
        """
        Trace affected shipments and customers.

        Logic:
        1. Find serial numbers produced from affected lots or work orders
        2. Find shipments containing these serial numbers
        3. Aggregate customer information
        """
        lot_ids = [lot.id for lot in lot_batches]
        wo_ids = [wo.work_order_id for wo in affected_work_orders]

        # Find serial numbers linked to affected lots or work orders
        serial_numbers_query = self.db.query(SerialNumber).filter(
            or_(
                SerialNumber.lot_batch_id.in_(lot_ids),
                SerialNumber.work_order_id.in_(wo_ids)
            )
        )

        # Filter to shipped serial numbers
        serial_numbers = serial_numbers_query.filter(
            SerialNumber.status == 'SHIPPED'
        ).all()

        if not serial_numbers:
            logger.info("No shipped serial numbers found for affected lots/work orders")
            return [], []

        # Get shipment IDs from serial numbers
        shipment_ids = list(set(
            sn.shipment_id for sn in serial_numbers
            if sn.shipment_id is not None
        ))

        if not shipment_ids:
            logger.info("No shipments found for affected serial numbers")
            return [], []

        # Query shipments
        shipments = self.db.query(Shipment).filter(
            Shipment.id.in_(shipment_ids)
        ).all()

        # Build affected shipments list
        affected_shipments = []
        customer_data = {}  # For aggregating customer information

        for shipment in shipments:
            # Find serial numbers in this shipment
            shipment_serials = [
                sn for sn in serial_numbers
                if sn.shipment_id == shipment.id
            ]

            serial_nums = [sn.serial_number for sn in shipment_serials]
            quantity = Decimal(len(serial_nums))

            # Extract customer info from serial numbers or shipment metadata
            # Since we don't have a Customer table, use metadata from serial numbers
            customer_name = None
            customer_email = None

            if shipment_serials and include_customer_details:
                # Try to get customer info from first serial number's custom_attributes
                first_serial = shipment_serials[0]
                if first_serial.custom_attributes:
                    customer_name = first_serial.custom_attributes.get('customer_name')
                    customer_email = first_serial.custom_attributes.get('customer_email')

                # Fallback: use shipment destination as customer name
                if not customer_name and shipment.destination_location:
                    customer_name = shipment.destination_location

            affected_shipments.append(AffectedShipmentDTO(
                shipment_id=shipment.id,
                shipment_number=shipment.shipment_number,
                customer_name=customer_name,
                customer_email=customer_email,
                shipped_date=shipment.actual_ship_date,
                quantity=quantity,
                serial_numbers=serial_nums
            ))

            # Aggregate customer data
            if customer_name:
                if customer_name not in customer_data:
                    customer_data[customer_name] = {
                        'email': customer_email,
                        'total_quantity': Decimal(0),
                        'shipment_count': 0
                    }
                customer_data[customer_name]['total_quantity'] += quantity
                customer_data[customer_name]['shipment_count'] += 1

        # Build affected customers list
        affected_customers = [
            AffectedCustomerDTO(
                customer_name=name,
                customer_email=data['email'],
                total_quantity=data['total_quantity'],
                shipment_count=data['shipment_count']
            )
            for name, data in customer_data.items()
        ]

        return affected_shipments, affected_customers
