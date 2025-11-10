"""
Traceability Service - Business logic for lot/serial tracking and genealogy
"""
from typing import List, Optional, Dict, Set
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from decimal import Decimal

from app.models.traceability import (
    LotBatch,
    SerialNumber,
    TraceabilityLink,
    GenealogyRecord
)
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
)


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
