"""
Receive Material Use Case

Implements goods receipt workflow:
1. Validate material exists
2. Create inventory transaction (GOODS_RECEIPT)
3. Update inventory quantity
4. Trigger low stock check (via database trigger)
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


class ReceiveMaterialDTO:
    """Data Transfer Object for material receipt."""

    def __init__(
        self,
        material_id: int,
        storage_location_id: int,
        quantity: Decimal,
        batch_number: str,
        transaction_reference: str,  # e.g., "PO-12345"
        unit_cost: Optional[Decimal] = None,
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
        self.unit_cost = unit_cost
        self.transaction_date = transaction_date or datetime.now()
        self.notes = notes
        self.user_id = user_id
        self.organization_id = organization_id
        self.plant_id = plant_id


class ReceiveMaterialUseCase:
    """
    Use case for receiving material into inventory (goods receipt).

    Business Rules:
    - BR-MAT-007: Material must exist and be active
    - BR-MAT-008: Quantity must be positive
    - BR-MAT-009: Storage location must exist and be active
    - BR-MAT-010: Batch number is required
    - BR-MAT-011: Creates immutable transaction record
    - BR-MAT-012: Updates inventory quantity (creates if new batch)
    """

    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = InventoryTransactionRepository(db)
        self.inventory_repo = InventoryRepository(db)

    def execute(self, dto: ReceiveMaterialDTO) -> InventoryTransaction:
        """
        Execute material receipt.

        Args:
            dto: ReceiveMaterialDTO with receipt details

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

        if not material.is_active:
            raise ValidationException(
                f"Material '{material.material_code}' is inactive and cannot receive goods",
                field="material_id"
            )

        # 2. Validate quantity is positive
        if dto.quantity <= 0:
            raise ValidationException(
                "Quantity must be positive for goods receipt",
                field="quantity"
            )

        # 3. Validate storage location exists (RLS will filter by org/plant)
        from app.models.inventory import StorageLocation
        storage_location = self.db.query(StorageLocation).filter(
            StorageLocation.id == dto.storage_location_id
        ).first()

        if not storage_location:
            raise EntityNotFoundException(
                entity_type="StorageLocation",
                entity_id=dto.storage_location_id
            )

        if not storage_location.is_active:
            raise ValidationException(
                f"Storage location '{storage_location.location_code}' is inactive",
                field="storage_location_id"
            )

        # 4. Determine unit cost (use material's standard cost if not provided)
        unit_cost = float(dto.unit_cost) if dto.unit_cost else material.standard_cost
        if unit_cost is None:
            raise ValidationException(
                "Unit cost is required. Material has no standard cost defined.",
                field="unit_cost"
            )

        # 5. Create inventory transaction (immutable audit record)
        transaction = InventoryTransaction(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            material_id=dto.material_id,
            storage_location_id=dto.storage_location_id,
            transaction_type=TransactionType.GOODS_RECEIPT,
            transaction_reference=dto.transaction_reference,
            batch_number=dto.batch_number,
            quantity=float(dto.quantity),  # Positive for receipts
            unit_of_measure_id=material.unit_of_measure_id,
            unit_cost=unit_cost,
            total_value=unit_cost * float(dto.quantity),
            transaction_date=dto.transaction_date,
            posted_by_user_id=dto.user_id,
            notes=dto.notes
        )

        created_transaction = self.transaction_repo.create(transaction)

        # 6. Update inventory quantity (creates new record if batch doesn't exist)
        self.inventory_repo.create_or_update(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            material_id=dto.material_id,
            storage_location_id=dto.storage_location_id,
            batch_number=dto.batch_number,
            quantity_change=float(dto.quantity),  # Add to inventory
            unit_of_measure_id=material.unit_of_measure_id
        )

        # 7. Update material's quantity_on_hand (aggregated across all locations/batches)
        material.quantity_on_hand = (material.quantity_on_hand or 0) + float(dto.quantity)
        self.db.commit()

        # Note: Low stock check trigger will fire automatically if quantity crosses reorder point

        return created_transaction
