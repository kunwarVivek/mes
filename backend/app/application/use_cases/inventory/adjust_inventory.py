"""
Adjust Inventory Use Case

Implements inventory adjustment workflow (physical count corrections):
1. Validate material and location exist
2. Calculate adjustment quantity (target - current)
3. Create inventory transaction (ADJUSTMENT)
4. Update inventory to target quantity
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.models.inventory import InventoryTransaction, TransactionType
from app.models.material import Material
from app.infrastructure.repositories.inventory_repository import (
    InventoryTransactionRepository,
    InventoryRepository
)
from app.core.exceptions import (
    EntityNotFoundException,
    ValidationException
)


class AdjustInventoryDTO:
    """Data Transfer Object for inventory adjustment."""

    def __init__(
        self,
        material_id: int,
        storage_location_id: int,
        batch_number: str,
        target_quantity: Decimal,  # New quantity after adjustment
        reason: str,  # "PHYSICAL_COUNT", "DAMAGE", "OBSOLETE", "FOUND", etc.
        transaction_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        user_id: int = None,
        organization_id: int = None,
        plant_id: int = None
    ):
        self.material_id = material_id
        self.storage_location_id = storage_location_id
        self.batch_number = batch_number
        self.target_quantity = target_quantity
        self.reason = reason
        self.transaction_date = transaction_date or datetime.now()
        self.notes = notes
        self.user_id = user_id
        self.organization_id = organization_id
        self.plant_id = plant_id


class AdjustInventoryUseCase:
    """
    Use case for adjusting inventory (physical count corrections).

    Business Rules:
    - BR-MAT-017: Adjustment can be positive (found) or negative (loss/damage)
    - BR-MAT-018: Target quantity must be non-negative
    - BR-MAT-019: Reason code is required for audit
    - BR-MAT-020: Creates immutable transaction record
    """

    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = InventoryTransactionRepository(db)
        self.inventory_repo = InventoryRepository(db)

    def execute(self, dto: AdjustInventoryDTO) -> InventoryTransaction:
        """
        Execute inventory adjustment.

        Args:
            dto: AdjustInventoryDTO with adjustment details

        Returns:
            Created InventoryTransaction

        Raises:
            EntityNotFoundException: If material or location not found
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

        # 2. Validate target quantity is non-negative (BR-MAT-018)
        if dto.target_quantity < 0:
            raise ValidationException(
                "Target quantity cannot be negative",
                field="target_quantity"
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

        # 4. Get current inventory (or create if doesn't exist)
        inventory = self.inventory_repo.get_by_material_and_location(
            material_id=dto.material_id,
            storage_location_id=dto.storage_location_id,
            batch_number=dto.batch_number
        )

        current_quantity = inventory.quantity_on_hand if inventory else 0.0

        # 5. Calculate adjustment quantity (positive = increase, negative = decrease)
        adjustment_quantity = float(dto.target_quantity) - current_quantity

        # If no change, skip transaction
        if adjustment_quantity == 0:
            raise ValidationException(
                f"No adjustment needed. Current quantity already equals target ({current_quantity})",
                field="target_quantity"
            )

        # 6. Determine unit cost (use material's standard cost or weighted average)
        unit_cost = material.standard_cost or 0.0

        # 7. Create inventory transaction (immutable audit record)
        transaction = InventoryTransaction(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            material_id=dto.material_id,
            storage_location_id=dto.storage_location_id,
            transaction_type=TransactionType.ADJUSTMENT,
            transaction_reference=f"ADJ-{dto.reason}",
            batch_number=dto.batch_number,
            quantity=adjustment_quantity,  # Positive or negative
            unit_of_measure_id=material.unit_of_measure_id,
            unit_cost=unit_cost,
            total_value=unit_cost * abs(adjustment_quantity),
            transaction_date=dto.transaction_date,
            posted_by_user_id=dto.user_id,
            notes=f"Reason: {dto.reason}. {dto.notes or ''}"
        )

        created_transaction = self.transaction_repo.create(transaction)

        # 8. Update inventory to target quantity
        self.inventory_repo.create_or_update(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            material_id=dto.material_id,
            storage_location_id=dto.storage_location_id,
            batch_number=dto.batch_number,
            quantity_change=adjustment_quantity,
            unit_of_measure_id=material.unit_of_measure_id
        )

        # 9. Update material's aggregated quantity_on_hand
        material.quantity_on_hand = (material.quantity_on_hand or 0) + adjustment_quantity
        self.db.commit()

        return created_transaction
