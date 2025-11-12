"""
WorkOrderRepository - Infrastructure layer repository for Work Order entities.

Handles database operations for Work Order production planning with:
- CRUD operations with domain validation
- RLS-aware queries (context set automatically by get_db())
- Pagination and filtering
- State transition management (PLANNED -> RELEASED -> IN_PROGRESS -> PAUSED -> COMPLETED)
- Pause/Resume operations for work order management
- Enhanced cancel with material release functionality
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, func
from datetime import datetime
import logging

from app.models.work_order import WorkOrder, WorkOrderOperation, WorkOrderMaterial, WorkCenter
from app.models.work_order import OrderType, OrderStatus, OperationStatus
from app.models.material import Material
from app.domain.entities.work_order import WorkOrderDomain, WorkOrderOperationDomain


logger = logging.getLogger(__name__)


class WorkOrderRepository:
    """
    Repository for Work Order entity persistence.

    Provides CRUD operations, state transitions, and search functionality.
    RLS context is automatically applied from database session.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session with RLS context
        """
        self._db = db

    def create(self, work_order_data: dict) -> WorkOrder:
        """
        Create new work order with domain validation.

        Args:
            work_order_data: Dictionary with work order attributes

        Returns:
            Created WorkOrder entity

        Raises:
            ValueError: If validation fails or work order number exists
        """
        # Domain validation
        domain_work_order = WorkOrderDomain(
            id=None,
            organization_id=work_order_data["organization_id"],
            plant_id=work_order_data["plant_id"],
            work_order_number=work_order_data["work_order_number"],
            material_id=work_order_data["material_id"],
            order_type=work_order_data["order_type"],
            order_status=work_order_data["order_status"],
            planned_quantity=work_order_data["planned_quantity"],
            actual_quantity=work_order_data.get("actual_quantity", 0.0),
            start_date_planned=work_order_data.get("start_date_planned"),
            end_date_planned=work_order_data.get("end_date_planned"),
            priority=work_order_data["priority"],
            created_by_user_id=work_order_data["created_by_user_id"]
        )

        # Create database model
        db_work_order = WorkOrder(
            organization_id=work_order_data["organization_id"],
            plant_id=work_order_data["plant_id"],
            work_order_number=work_order_data["work_order_number"],
            material_id=work_order_data["material_id"],
            order_type=OrderType(work_order_data["order_type"]),
            order_status=OrderStatus(work_order_data["order_status"]),
            planned_quantity=work_order_data["planned_quantity"],
            actual_quantity=work_order_data.get("actual_quantity", 0.0),
            start_date_planned=work_order_data.get("start_date_planned"),
            end_date_planned=work_order_data.get("end_date_planned"),
            priority=work_order_data["priority"],
            created_by_user_id=work_order_data["created_by_user_id"]
        )

        try:
            self._db.add(db_work_order)
            self._db.commit()
            self._db.refresh(db_work_order)
            logger.info(f"Created work order: {db_work_order.work_order_number}")
            return db_work_order
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to create work order: {e}")
            raise ValueError(f"Work order number {work_order_data['work_order_number']} already exists")

    def get_by_id(self, work_order_id: int) -> Optional[WorkOrder]:
        """
        Retrieve work order by ID with operations and materials.

        RLS filtering is automatic from session context.

        Args:
            work_order_id: Work Order ID

        Returns:
            WorkOrder entity or None if not found
        """
        return (
            self._db.query(WorkOrder)
            .options(
                joinedload(WorkOrder.operations),
                joinedload(WorkOrder.materials)
            )
            .filter(WorkOrder.id == work_order_id)
            .first()
        )

    def get_by_number(
        self, org_id: int, plant_id: int, work_order_number: str
    ) -> Optional[WorkOrder]:
        """
        Retrieve work order by unique work_order_number within org/plant.

        Args:
            org_id: Organization ID
            plant_id: Plant ID
            work_order_number: Work order number (unique)

        Returns:
            WorkOrder entity or None if not found
        """
        return (
            self._db.query(WorkOrder)
            .filter(WorkOrder.organization_id == org_id)
            .filter(WorkOrder.plant_id == plant_id)
            .filter(WorkOrder.work_order_number == work_order_number)
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
        List work orders with pagination and filtering.

        Args:
            org_id: Organization ID
            plant_id: Optional plant ID filter
            filters: Optional filters (status, material_id, priority, date_from, date_to)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with items, total, page, page_size, total_pages
        """
        query = self._db.query(WorkOrder).filter(WorkOrder.organization_id == org_id)

        if plant_id is not None:
            query = query.filter(WorkOrder.plant_id == plant_id)

        # Apply filters
        if filters:
            if "status" in filters:
                query = query.filter(WorkOrder.order_status == OrderStatus(filters["status"]))
            if "material_id" in filters:
                query = query.filter(WorkOrder.material_id == filters["material_id"])
            if "priority" in filters:
                query = query.filter(WorkOrder.priority == filters["priority"])
            if "date_from" in filters:
                query = query.filter(WorkOrder.start_date_planned >= filters["date_from"])
            if "date_to" in filters:
                query = query.filter(WorkOrder.end_date_planned <= filters["date_to"])

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def update(self, work_order_id: int, updates: dict) -> WorkOrder:
        """
        Update work order with validation.

        Args:
            work_order_id: Work Order ID to update
            updates: Dictionary with fields to update

        Returns:
            Updated WorkOrder entity

        Raises:
            ValueError: If work order not found or validation fails
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            raise ValueError(f"Work order with id {work_order_id} not found")

        # Update allowed fields
        updatable_fields = [
            "planned_quantity",
            "start_date_planned",
            "end_date_planned",
            "priority",
        ]

        for field, value in updates.items():
            if field in updatable_fields:
                setattr(db_work_order, field, value)

        self._db.commit()
        self._db.refresh(db_work_order)
        logger.info(f"Updated work order: {db_work_order.work_order_number}")
        return db_work_order

    def cancel(self, work_order_id: int) -> bool:
        """
        Cancel work order (soft delete - set status=CANCELLED).

        Args:
            work_order_id: Work Order ID to cancel

        Returns:
            True if cancelled, False if not found

        Raises:
            ValueError: If already cancelled or completed
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            return False

        if db_work_order.order_status == OrderStatus.CANCELLED:
            raise ValueError("Work order is already cancelled")

        if db_work_order.order_status == OrderStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed work order")

        db_work_order.order_status = OrderStatus.CANCELLED
        self._db.commit()
        logger.info(f"Cancelled work order: {db_work_order.work_order_number}")
        return True

    def release(self, work_order_id: int) -> WorkOrder:
        """
        Release work order (PLANNED -> RELEASED).

        Args:
            work_order_id: Work Order ID to release

        Returns:
            Released WorkOrder entity

        Raises:
            ValueError: If not in PLANNED status
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            raise ValueError(f"Work order with id {work_order_id} not found")

        if db_work_order.order_status != OrderStatus.PLANNED:
            raise ValueError("Work order can only be released from PLANNED status")

        db_work_order.order_status = OrderStatus.RELEASED
        self._db.commit()
        self._db.refresh(db_work_order)
        logger.info(f"Released work order: {db_work_order.work_order_number}")
        return db_work_order

    def start(self, work_order_id: int) -> WorkOrder:
        """
        Start work order (RELEASED -> IN_PROGRESS).

        Args:
            work_order_id: Work Order ID to start

        Returns:
            Started WorkOrder entity

        Raises:
            ValueError: If not in RELEASED status
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            raise ValueError(f"Work order with id {work_order_id} not found")

        if db_work_order.order_status != OrderStatus.RELEASED:
            raise ValueError("Work order can only be started from RELEASED status")

        db_work_order.order_status = OrderStatus.IN_PROGRESS
        db_work_order.start_date_actual = datetime.utcnow()
        self._db.commit()
        self._db.refresh(db_work_order)
        logger.info(f"Started work order: {db_work_order.work_order_number}")
        return db_work_order

    def complete(self, work_order_id: int) -> WorkOrder:
        """
        Complete work order (IN_PROGRESS -> COMPLETED).

        Args:
            work_order_id: Work Order ID to complete

        Returns:
            Completed WorkOrder entity

        Raises:
            ValueError: If not in IN_PROGRESS status
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            raise ValueError(f"Work order with id {work_order_id} not found")

        if db_work_order.order_status != OrderStatus.IN_PROGRESS:
            raise ValueError("Work order can only be completed from IN_PROGRESS status")

        db_work_order.order_status = OrderStatus.COMPLETED
        db_work_order.end_date_actual = datetime.utcnow()
        self._db.commit()
        self._db.refresh(db_work_order)
        logger.info(f"Completed work order: {db_work_order.work_order_number}")
        return db_work_order

    def pause(self, work_order_id: int, reason: Optional[str] = None) -> WorkOrder:
        """
        Pause work order (IN_PROGRESS -> PAUSED).

        Args:
            work_order_id: Work Order ID to pause
            reason: Optional reason for pausing

        Returns:
            Paused WorkOrder entity

        Raises:
            ValueError: If work order not found or not in IN_PROGRESS status
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            raise ValueError(f"Work order with id {work_order_id} not found")

        if db_work_order.order_status != OrderStatus.IN_PROGRESS:
            raise ValueError("Work order can only be paused from IN_PROGRESS status")

        db_work_order.order_status = OrderStatus.PAUSED
        self._db.commit()
        self._db.refresh(db_work_order)
        logger.info(f"Paused work order: {db_work_order.work_order_number}" + (f" - Reason: {reason}" if reason else ""))
        return db_work_order

    def resume(self, work_order_id: int) -> WorkOrder:
        """
        Resume work order (PAUSED -> IN_PROGRESS).

        Args:
            work_order_id: Work Order ID to resume

        Returns:
            Resumed WorkOrder entity

        Raises:
            ValueError: If work order not found or not in PAUSED status
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            raise ValueError(f"Work order with id {work_order_id} not found")

        if db_work_order.order_status != OrderStatus.PAUSED:
            raise ValueError("Work order can only be resumed from PAUSED status")

        db_work_order.order_status = OrderStatus.IN_PROGRESS
        self._db.commit()
        self._db.refresh(db_work_order)
        logger.info(f"Resumed work order: {db_work_order.work_order_number}")
        return db_work_order

    def cancel_with_materials(
        self, work_order_id: int, reason: str, cancel_materials: bool = True
    ) -> WorkOrder:
        """
        Cancel work order with optional material release (any status -> CANCELLED).

        Args:
            work_order_id: Work Order ID to cancel
            reason: Required reason for cancellation
            cancel_materials: Whether to release/unreserve reserved materials (default: True)

        Returns:
            Cancelled WorkOrder entity

        Raises:
            ValueError: If work order not found or already COMPLETED/CANCELLED
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            raise ValueError(f"Work order with id {work_order_id} not found")

        if db_work_order.order_status == OrderStatus.CANCELLED:
            raise ValueError("Work order is already cancelled")

        if db_work_order.order_status == OrderStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed work order")

        # Update status to CANCELLED
        db_work_order.order_status = OrderStatus.CANCELLED

        # If cancel_materials is True, release any reserved materials
        # This would involve updating material reservations/inventory
        # For now, we'll log the intent - actual implementation would involve
        # querying WorkOrderMaterial records and creating reversal transactions
        if cancel_materials:
            logger.info(f"Releasing materials for cancelled work order: {db_work_order.work_order_number}")
            # TODO: Implement material release logic here
            # This would typically involve:
            # 1. Query all WorkOrderMaterial records for this work order
            # 2. For each material with reserved quantity, create reversal transactions
            # 3. Update inventory availability

        self._db.commit()
        self._db.refresh(db_work_order)
        logger.info(f"Cancelled work order: {db_work_order.work_order_number} - Reason: {reason}")
        return db_work_order

    def add_operation(self, work_order_id: int, operation_data: dict) -> WorkOrderOperation:
        """
        Add operation to work order.

        Args:
            work_order_id: Work Order ID
            operation_data: Operation details

        Returns:
            Created WorkOrderOperation entity

        Raises:
            ValueError: If work order not found or validation fails
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            raise ValueError(f"Work order with id {work_order_id} not found")

        # Domain validation
        domain_operation = WorkOrderOperationDomain(
            id=None,
            organization_id=db_work_order.organization_id,
            plant_id=db_work_order.plant_id,
            work_order_id=work_order_id,
            operation_number=operation_data["operation_number"],
            operation_name=operation_data["operation_name"],
            work_center_id=operation_data["work_center_id"],
            setup_time_minutes=operation_data.get("setup_time_minutes", 0.0),
            run_time_per_unit_minutes=operation_data.get("run_time_per_unit_minutes", 0.0),
            status="PENDING"
        )

        # Create operation
        db_operation = WorkOrderOperation(
            organization_id=db_work_order.organization_id,
            plant_id=db_work_order.plant_id,
            work_order_id=work_order_id,
            operation_number=operation_data["operation_number"],
            operation_name=operation_data["operation_name"],
            work_center_id=operation_data["work_center_id"],
            setup_time_minutes=operation_data.get("setup_time_minutes", 0.0),
            run_time_per_unit_minutes=operation_data.get("run_time_per_unit_minutes", 0.0),
            status=OperationStatus.PENDING
        )

        try:
            self._db.add(db_operation)
            self._db.commit()
            self._db.refresh(db_operation)
            logger.info(f"Added operation {operation_data['operation_number']} to work order {work_order_id}")
            return db_operation
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to add operation: {e}")
            raise ValueError(f"Operation number {operation_data['operation_number']} already exists for this work order")

    def add_material(self, work_order_id: int, material_data: dict) -> WorkOrderMaterial:
        """
        Add material consumption to work order.

        Args:
            work_order_id: Work Order ID
            material_data: Material consumption details

        Returns:
            Created WorkOrderMaterial entity

        Raises:
            ValueError: If work order or material not found
        """
        db_work_order = self._db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not db_work_order:
            raise ValueError(f"Work order with id {work_order_id} not found")

        # Verify material exists
        db_material = self._db.query(Material).filter(Material.id == material_data["material_id"]).first()
        if not db_material:
            raise ValueError(f"Material with id {material_data['material_id']} not found")

        # Create material consumption record
        db_wo_material = WorkOrderMaterial(
            work_order_id=work_order_id,
            material_id=material_data["material_id"],
            planned_quantity=material_data["planned_quantity"],
            actual_quantity=0.0,
            unit_of_measure_id=material_data["unit_of_measure_id"],
            backflush=material_data.get("backflush", False)
        )

        self._db.add(db_wo_material)
        self._db.commit()
        self._db.refresh(db_wo_material)
        logger.info(f"Added material {material_data['material_id']} to work order {work_order_id}")
        return db_wo_material
