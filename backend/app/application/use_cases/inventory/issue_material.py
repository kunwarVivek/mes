"""
Issue Material Use Case

Implements goods issue workflow:
1. Validate material exists and has sufficient quantity
2. Create inventory transaction (GOODS_ISSUE)
3. Update inventory quantity
4. Calculate cost using FIFO/LIFO/Weighted Average
5. Update work order actual_material_cost (if reference is work order)
6. Trigger low stock alert (via database trigger if threshold crossed)
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.models.inventory import InventoryTransaction, TransactionType
from app.models.material import Material
from app.models.work_order import WorkOrder
from app.infrastructure.repositories.inventory_repository import (
    InventoryTransactionRepository,
    InventoryRepository
)
from app.application.services.costing_service import CostingService
from app.core.exceptions import (
    EntityNotFoundException,
    ValidationException,
    InsufficientInventoryException,
    BusinessRuleViolationException
)


class IssueMaterialDTO:
    """Data Transfer Object for material issue."""

    def __init__(
        self,
        material_id: int,
        storage_location_id: int,
        quantity: Decimal,
        batch_number: str,
        transaction_reference: str,  # e.g., "WO-00123"
        reference_type: str,  # "WORK_ORDER", "SALES_ORDER", "MAINTENANCE", etc.
        reference_id: Optional[int] = None,  # Work order ID, etc.
        transaction_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        user_id: int = None,
        organization_id: int = None,
        plant_id: int = None
    ):
        self.material_id = material_id
        self.storage_location_id = storage_location_id
        self.quantity = quantity
        self.batch_number = batch_number
        self.transaction_reference = transaction_reference
        self.reference_type = reference_type
        self.reference_id = reference_id
        self.transaction_date = transaction_date or datetime.now()
        self.notes = notes
        self.user_id = user_id
        self.organization_id = organization_id
        self.plant_id = plant_id


class IssueMaterialUseCase:
    """
    Use case for issuing material from inventory (goods issue).

    Business Rules:
    - BR-MAT-002: Prevent negative inventory (quantity_on_hand >= 0)
    - BR-MAT-013: Validate sufficient available quantity
    - BR-MAT-014: Use organization's costing method (FIFO/LIFO/Weighted Average)
    - BR-MAT-015: Update work order actual_material_cost for WO references
    - BR-MAT-016: Trigger low stock alert if threshold crossed
    """

    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = InventoryTransactionRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.costing_service = CostingService(db)

    def execute(self, dto: IssueMaterialDTO) -> InventoryTransaction:
        """
        Execute material issue.

        Args:
            dto: IssueMaterialDTO with issue details

        Returns:
            Created InventoryTransaction

        Raises:
            EntityNotFoundException: If material or location not found
            InsufficientInventoryException: If quantity exceeds available
            ValidationException: If validation fails
        """
        # 1. Validate material exists and is active
        material = self.db.query(Material).filter(
            Material.id == dto.material_id
        ).first()

        if not material:
            raise EntityNotFoundException(
                entity_type="Material",
                entity_id=dto.material_id
            )

        if not material.is_active:
            raise ValidationException(
                f"Material '{material.material_code}' is inactive",
                field="material_id"
            )

        # 2. Validate quantity is positive
        if dto.quantity <= 0:
            raise ValidationException(
                "Quantity must be positive for goods issue",
                field="quantity"
            )

        # 3. Validate storage location exists
        from app.models.inventory import StorageLocation
        storage_location = self.db.query(StorageLocation).filter(
            StorageLocation.id == dto.storage_location_id
        ).first()

        if not storage_location:
            raise EntityNotFoundException(
                entity_type="StorageLocation",
                entity_id=dto.storage_location_id
            )

        # 4. Validate sufficient inventory
        inventory = self.inventory_repo.get_by_material_and_location(
            material_id=dto.material_id,
            storage_location_id=dto.storage_location_id,
            batch_number=dto.batch_number
        )

        if not inventory:
            raise InsufficientInventoryException(
                material_code=material.material_code,
                requested=float(dto.quantity),
                available=0.0
            )

        available_quantity = inventory.quantity_on_hand - inventory.quantity_reserved

        if float(dto.quantity) > available_quantity:
            raise InsufficientInventoryException(
                material_code=material.material_code,
                requested=float(dto.quantity),
                available=available_quantity
            )

        # 5. Calculate cost using organization's costing method (FIFO/LIFO/Weighted Average)
        # Get material's costing method from organization settings or default to FIFO
        from app.models.organization import Organization
        org = self.db.query(Organization).filter(
            Organization.id == dto.organization_id
        ).first()

        costing_method = org.costing_method if org and hasattr(org, 'costing_method') else "FIFO"

        # Calculate unit cost based on costing method
        try:
            unit_cost = self.costing_service.calculate_issue_cost(
                material_id=dto.material_id,
                quantity=float(dto.quantity),
                costing_method=costing_method
            )
        except Exception as e:
            # Fallback to material's standard cost if costing calculation fails
            unit_cost = material.standard_cost or 0.0
            if unit_cost == 0.0:
                raise ValidationException(
                    f"Cannot determine cost for material '{material.material_code}'. "
                    f"Costing calculation failed and no standard cost defined.",
                    field="unit_cost"
                )

        # 6. Create inventory transaction (immutable audit record)
        transaction = InventoryTransaction(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            material_id=dto.material_id,
            storage_location_id=dto.storage_location_id,
            transaction_type=TransactionType.GOODS_ISSUE,
            transaction_reference=dto.transaction_reference,
            batch_number=dto.batch_number,
            quantity=float(dto.quantity),  # Positive value (quantity consumed)
            unit_of_measure_id=material.unit_of_measure_id,
            unit_cost=unit_cost,
            total_value=unit_cost * float(dto.quantity),
            transaction_date=dto.transaction_date,
            posted_by_user_id=dto.user_id,
            notes=dto.notes
        )

        created_transaction = self.transaction_repo.create(transaction)

        # 7. Update inventory quantity (subtract from inventory)
        self.inventory_repo.create_or_update(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            material_id=dto.material_id,
            storage_location_id=dto.storage_location_id,
            batch_number=dto.batch_number,
            quantity_change=-float(dto.quantity),  # Negative to reduce inventory
            unit_of_measure_id=material.unit_of_measure_id
        )

        # 8. Update material's aggregated quantity_on_hand
        material.quantity_on_hand = (material.quantity_on_hand or 0) - float(dto.quantity)

        # Ensure quantity doesn't go negative (business rule BR-MAT-002)
        if material.quantity_on_hand < 0:
            self.db.rollback()
            raise BusinessRuleViolationException(
                rule="BR-MAT-002",
                message=f"Operation would result in negative inventory for material '{material.material_code}'"
            )

        self.db.commit()

        # 9. Update work order actual_material_cost if reference is work order
        if dto.reference_type == "WORK_ORDER" and dto.reference_id:
            self._update_work_order_cost(
                work_order_id=dto.reference_id,
                material_cost=unit_cost * float(dto.quantity)
            )

        # Note: Low stock alert trigger will fire automatically if quantity crosses reorder point

        return created_transaction

    def _update_work_order_cost(self, work_order_id: int, material_cost: float) -> None:
        """
        Update work order's actual_material_cost.

        Args:
            work_order_id: Work order ID
            material_cost: Material cost to add
        """
        work_order = self.db.query(WorkOrder).filter(
            WorkOrder.id == work_order_id
        ).first()

        if work_order:
            work_order.actual_material_cost = (work_order.actual_material_cost or 0) + material_cost
            self.db.commit()
