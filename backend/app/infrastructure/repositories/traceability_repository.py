"""
Repository for Traceability (Lot/Batch, Serial Numbers, Links, Genealogy)
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func, asc
from datetime import datetime, timezone, date

from app.models.traceability import (
    LotBatch,
    SerialNumber,
    TraceabilityLink,
    GenealogyRecord
)
from app.application.dtos.traceability_dto import (
    LotBatchCreateDTO,
    LotBatchUpdateDTO,
    SerialNumberCreateDTO,
    SerialNumberUpdateDTO,
    TraceabilityLinkCreateDTO,
    GenealogyRecordCreateDTO,
)


class LotBatchRepository:
    """Repository for LotBatch operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: LotBatchCreateDTO) -> LotBatch:
        """Create a new lot batch"""
        lot = LotBatch(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            lot_number=dto.lot_number,
            material_id=dto.material_id,
            supplier_lot_number=dto.supplier_lot_number,
            initial_quantity=dto.initial_quantity,
            current_quantity=dto.initial_quantity,  # Start with initial quantity
            reserved_quantity=0,
            unit_of_measure=dto.unit_of_measure,
            source_type=dto.source_type,
            source_reference_id=dto.source_reference_id,
            supplier_id=dto.supplier_id,
            production_date=dto.production_date,
            received_date=dto.received_date,
            expiry_date=dto.expiry_date,
            retest_date=dto.retest_date,
            warehouse_location=dto.warehouse_location,
            bin_location=dto.bin_location,
            traceability_attributes=dto.traceability_attributes,
            custom_attributes=dto.custom_attributes,
            notes=dto.notes,
            created_by=dto.created_by,
        )
        self.db.add(lot)
        self.db.commit()
        self.db.refresh(lot)
        return lot

    def get_by_id(self, lot_id: int) -> Optional[LotBatch]:
        """Get lot batch by ID"""
        return self.db.query(LotBatch).filter(LotBatch.id == lot_id).first()

    def get_by_lot_number(self, organization_id: int, lot_number: str) -> Optional[LotBatch]:
        """Get lot batch by lot number"""
        return self.db.query(LotBatch).filter(
            and_(
                LotBatch.organization_id == organization_id,
                LotBatch.lot_number == lot_number
            )
        ).first()

    def list_by_organization(self, organization_id: int, skip: int = 0, limit: int = 100,
                            material_id: Optional[int] = None, quality_status: Optional[str] = None,
                            active_only: bool = True) -> List[LotBatch]:
        """List lot batches for an organization"""
        query = self.db.query(LotBatch).filter(
            LotBatch.organization_id == organization_id
        )

        if active_only:
            query = query.filter(LotBatch.is_active == True)

        if material_id:
            query = query.filter(LotBatch.material_id == material_id)

        if quality_status:
            query = query.filter(LotBatch.quality_status == quality_status)

        return query.order_by(desc(LotBatch.created_at)).offset(skip).limit(limit).all()

    def list_by_material(self, material_id: int, quality_status: Optional[str] = None,
                        available_only: bool = False) -> List[LotBatch]:
        """List lot batches for a material"""
        query = self.db.query(LotBatch).filter(
            and_(
                LotBatch.material_id == material_id,
                LotBatch.is_active == True
            )
        )

        if quality_status:
            query = query.filter(LotBatch.quality_status == quality_status)

        if available_only:
            query = query.filter(
                LotBatch.current_quantity > LotBatch.reserved_quantity
            )

        return query.order_by(LotBatch.lot_number).all()

    def list_expiring_soon(self, organization_id: int, days: int = 30) -> List[LotBatch]:
        """List lots expiring within specified days"""
        cutoff_date = date.today()
        future_date = date.fromordinal(cutoff_date.toordinal() + days)

        return self.db.query(LotBatch).filter(
            and_(
                LotBatch.organization_id == organization_id,
                LotBatch.is_active == True,
                LotBatch.expiry_date.isnot(None),
                LotBatch.expiry_date >= cutoff_date,
                LotBatch.expiry_date <= future_date
            )
        ).order_by(LotBatch.expiry_date).all()

    def list_needing_retest(self, organization_id: int) -> List[LotBatch]:
        """List lots needing retest"""
        today = date.today()

        return self.db.query(LotBatch).filter(
            and_(
                LotBatch.organization_id == organization_id,
                LotBatch.is_active == True,
                LotBatch.retest_date.isnot(None),
                LotBatch.retest_date <= today
            )
        ).order_by(LotBatch.retest_date).all()

    def update(self, lot_id: int, dto: LotBatchUpdateDTO) -> Optional[LotBatch]:
        """Update lot batch"""
        lot = self.get_by_id(lot_id)
        if not lot:
            return None

        if dto.current_quantity is not None:
            lot.current_quantity = dto.current_quantity
        if dto.reserved_quantity is not None:
            lot.reserved_quantity = dto.reserved_quantity
        if dto.quality_status is not None:
            lot.quality_status = dto.quality_status
        if dto.inspection_status is not None:
            lot.inspection_status = dto.inspection_status
        if dto.certificate_number is not None:
            lot.certificate_number = dto.certificate_number
        if dto.warehouse_location is not None:
            lot.warehouse_location = dto.warehouse_location
        if dto.bin_location is not None:
            lot.bin_location = dto.bin_location
        if dto.traceability_attributes is not None:
            lot.traceability_attributes = dto.traceability_attributes
        if dto.custom_attributes is not None:
            lot.custom_attributes = dto.custom_attributes
        if dto.notes is not None:
            lot.notes = dto.notes
        if dto.is_active is not None:
            lot.is_active = dto.is_active

        self.db.commit()
        self.db.refresh(lot)
        return lot

    def delete(self, lot_id: int) -> bool:
        """Delete lot batch (soft delete)"""
        lot = self.get_by_id(lot_id)
        if not lot:
            return False

        lot.is_active = False
        self.db.commit()
        return True


class SerialNumberRepository:
    """Repository for SerialNumber operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: SerialNumberCreateDTO) -> SerialNumber:
        """Create a new serial number"""
        serial = SerialNumber(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            serial_number=dto.serial_number,
            material_id=dto.material_id,
            lot_batch_id=dto.lot_batch_id,
            work_order_id=dto.work_order_id,
            production_date=dto.production_date,
            production_line=dto.production_line,
            warehouse_location=dto.warehouse_location,
            traceability_attributes=dto.traceability_attributes,
            custom_attributes=dto.custom_attributes,
            notes=dto.notes,
            created_by=dto.created_by,
        )
        self.db.add(serial)
        self.db.commit()
        self.db.refresh(serial)
        return serial

    def get_by_id(self, serial_id: int) -> Optional[SerialNumber]:
        """Get serial number by ID"""
        return self.db.query(SerialNumber).filter(SerialNumber.id == serial_id).first()

    def get_by_serial_number(self, organization_id: int, serial_number: str) -> Optional[SerialNumber]:
        """Get serial number by serial"""
        return self.db.query(SerialNumber).filter(
            and_(
                SerialNumber.organization_id == organization_id,
                SerialNumber.serial_number == serial_number
            )
        ).first()

    def list_by_organization(self, organization_id: int, skip: int = 0, limit: int = 100,
                            material_id: Optional[int] = None, status: Optional[str] = None,
                            customer_id: Optional[int] = None) -> List[SerialNumber]:
        """List serial numbers for an organization"""
        query = self.db.query(SerialNumber).filter(
            SerialNumber.organization_id == organization_id
        )

        if material_id:
            query = query.filter(SerialNumber.material_id == material_id)

        if status:
            query = query.filter(SerialNumber.status == status)

        if customer_id:
            query = query.filter(SerialNumber.customer_id == customer_id)

        return query.order_by(desc(SerialNumber.created_at)).offset(skip).limit(limit).all()

    def list_by_lot(self, lot_batch_id: int) -> List[SerialNumber]:
        """List serial numbers for a lot batch"""
        return self.db.query(SerialNumber).filter(
            SerialNumber.lot_batch_id == lot_batch_id
        ).order_by(SerialNumber.serial_number).all()

    def list_by_work_order(self, work_order_id: int) -> List[SerialNumber]:
        """List serial numbers produced in a work order"""
        return self.db.query(SerialNumber).filter(
            SerialNumber.work_order_id == work_order_id
        ).order_by(SerialNumber.serial_number).all()

    def list_by_customer(self, customer_id: int, skip: int = 0, limit: int = 100) -> List[SerialNumber]:
        """List serial numbers for a customer"""
        return self.db.query(SerialNumber).filter(
            SerialNumber.customer_id == customer_id
        ).order_by(desc(SerialNumber.shipped_date)).offset(skip).limit(limit).all()

    def list_in_warranty(self, organization_id: int) -> List[SerialNumber]:
        """List serial numbers currently under warranty"""
        today = date.today()

        return self.db.query(SerialNumber).filter(
            and_(
                SerialNumber.organization_id == organization_id,
                SerialNumber.warranty_end_date.isnot(None),
                SerialNumber.warranty_end_date >= today
            )
        ).order_by(SerialNumber.warranty_end_date).all()

    def update(self, serial_id: int, dto: SerialNumberUpdateDTO) -> Optional[SerialNumber]:
        """Update serial number"""
        serial = self.get_by_id(serial_id)
        if not serial:
            return None

        if dto.status is not None:
            serial.status = dto.status
        if dto.quality_status is not None:
            serial.quality_status = dto.quality_status
        if dto.current_location is not None:
            serial.current_location = dto.current_location
        if dto.warehouse_location is not None:
            serial.warehouse_location = dto.warehouse_location
        if dto.customer_id is not None:
            serial.customer_id = dto.customer_id
        if dto.shipment_id is not None:
            serial.shipment_id = dto.shipment_id
        if dto.shipped_date is not None:
            serial.shipped_date = dto.shipped_date
        if dto.installation_date is not None:
            serial.installation_date = dto.installation_date
        if dto.installation_location is not None:
            serial.installation_location = dto.installation_location
        if dto.warranty_start_date is not None:
            serial.warranty_start_date = dto.warranty_start_date
        if dto.warranty_end_date is not None:
            serial.warranty_end_date = dto.warranty_end_date
        if dto.last_service_date is not None:
            serial.last_service_date = dto.last_service_date
        if dto.traceability_attributes is not None:
            serial.traceability_attributes = dto.traceability_attributes
        if dto.custom_attributes is not None:
            serial.custom_attributes = dto.custom_attributes
        if dto.notes is not None:
            serial.notes = dto.notes

        self.db.commit()
        self.db.refresh(serial)
        return serial

    def delete(self, serial_id: int) -> bool:
        """Delete serial number (soft delete)"""
        serial = self.get_by_id(serial_id)
        if not serial:
            return False

        serial.is_active = False
        self.db.commit()
        return True


class TraceabilityLinkRepository:
    """Repository for TraceabilityLink operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: TraceabilityLinkCreateDTO) -> TraceabilityLink:
        """Create a new traceability link"""
        link = TraceabilityLink(
            organization_id=dto.organization_id,
            parent_type=dto.parent_type,
            parent_lot_id=dto.parent_lot_id,
            parent_serial_id=dto.parent_serial_id,
            child_type=dto.child_type,
            child_lot_id=dto.child_lot_id,
            child_serial_id=dto.child_serial_id,
            relationship_type=dto.relationship_type,
            quantity_used=dto.quantity_used,
            unit_of_measure=dto.unit_of_measure,
            work_order_id=dto.work_order_id,
            operation_sequence=dto.operation_sequence,
            link_date=dto.link_date,
            metadata=dto.metadata,
            created_by=dto.created_by,
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def get_by_id(self, link_id: int) -> Optional[TraceabilityLink]:
        """Get traceability link by ID"""
        return self.db.query(TraceabilityLink).filter(TraceabilityLink.id == link_id).first()

    def list_by_parent_lot(self, parent_lot_id: int) -> List[TraceabilityLink]:
        """List all links where this lot is the parent"""
        return self.db.query(TraceabilityLink).filter(
            TraceabilityLink.parent_lot_id == parent_lot_id
        ).order_by(desc(TraceabilityLink.link_date)).all()

    def list_by_parent_serial(self, parent_serial_id: int) -> List[TraceabilityLink]:
        """List all links where this serial is the parent"""
        return self.db.query(TraceabilityLink).filter(
            TraceabilityLink.parent_serial_id == parent_serial_id
        ).order_by(desc(TraceabilityLink.link_date)).all()

    def list_by_child_lot(self, child_lot_id: int) -> List[TraceabilityLink]:
        """List all links where this lot is the child"""
        return self.db.query(TraceabilityLink).filter(
            TraceabilityLink.child_lot_id == child_lot_id
        ).order_by(desc(TraceabilityLink.link_date)).all()

    def list_by_child_serial(self, child_serial_id: int) -> List[TraceabilityLink]:
        """List all links where this serial is the child"""
        return self.db.query(TraceabilityLink).filter(
            TraceabilityLink.child_serial_id == child_serial_id
        ).order_by(desc(TraceabilityLink.link_date)).all()

    def list_by_work_order(self, work_order_id: int) -> List[TraceabilityLink]:
        """List all links for a work order"""
        return self.db.query(TraceabilityLink).filter(
            TraceabilityLink.work_order_id == work_order_id
        ).order_by(TraceabilityLink.operation_sequence, TraceabilityLink.link_date).all()


class GenealogyRecordRepository:
    """Repository for GenealogyRecord operations (TimescaleDB hypertable)"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: GenealogyRecordCreateDTO) -> GenealogyRecord:
        """Create a new genealogy record"""
        record = GenealogyRecord(
            organization_id=dto.organization_id,
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            entity_identifier=dto.entity_identifier,
            operation_type=dto.operation_type,
            operation_timestamp=dto.operation_timestamp,
            work_order_id=dto.work_order_id,
            reference_type=dto.reference_type,
            reference_id=dto.reference_id,
            quantity_before=dto.quantity_before,
            quantity_after=dto.quantity_after,
            quantity_change=dto.quantity_change,
            status_before=dto.status_before,
            status_after=dto.status_after,
            location_before=dto.location_before,
            location_after=dto.location_after,
            metadata=dto.metadata,
            performed_by=dto.performed_by,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_id(self, record_id: int, operation_timestamp: datetime) -> Optional[GenealogyRecord]:
        """Get genealogy record by composite key (TimescaleDB requirement)"""
        return self.db.query(GenealogyRecord).filter(
            and_(
                GenealogyRecord.id == record_id,
                GenealogyRecord.operation_timestamp == operation_timestamp
            )
        ).first()

    def list_by_entity(self, entity_type: str, entity_identifier: str,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       skip: int = 0, limit: int = 100) -> List[GenealogyRecord]:
        """List genealogy records for an entity"""
        query = self.db.query(GenealogyRecord).filter(
            and_(
                GenealogyRecord.entity_type == entity_type,
                GenealogyRecord.entity_identifier == entity_identifier
            )
        )

        if start_date:
            query = query.filter(GenealogyRecord.operation_timestamp >= start_date)
        if end_date:
            query = query.filter(GenealogyRecord.operation_timestamp <= end_date)

        return query.order_by(desc(GenealogyRecord.operation_timestamp)).offset(skip).limit(limit).all()

    def list_by_operation_type(self, organization_id: int, operation_type: str,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               limit: int = 100) -> List[GenealogyRecord]:
        """List genealogy records by operation type"""
        query = self.db.query(GenealogyRecord).filter(
            and_(
                GenealogyRecord.organization_id == organization_id,
                GenealogyRecord.operation_type == operation_type
            )
        )

        if start_date:
            query = query.filter(GenealogyRecord.operation_timestamp >= start_date)
        if end_date:
            query = query.filter(GenealogyRecord.operation_timestamp <= end_date)

        return query.order_by(desc(GenealogyRecord.operation_timestamp)).limit(limit).all()

    def list_by_work_order(self, work_order_id: int) -> List[GenealogyRecord]:
        """List all genealogy records for a work order"""
        return self.db.query(GenealogyRecord).filter(
            GenealogyRecord.work_order_id == work_order_id
        ).order_by(GenealogyRecord.operation_timestamp).all()
