"""
Inventory Transaction Repository

Provides data access methods for inventory transactions.
Follows Repository pattern to abstract database operations.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.inventory import InventoryTransaction, TransactionType
from app.core.exceptions import EntityNotFoundException


class InventoryTransactionRepository:
    """
    Repository for InventoryTransaction entity.

    Provides CRUD operations and query methods for inventory transactions.
    All methods respect multi-tenant RLS context.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, transaction: InventoryTransaction) -> InventoryTransaction:
        """
        Create a new inventory transaction (immutable audit record).

        Args:
            transaction: InventoryTransaction entity to create

        Returns:
            Created transaction with ID populated
        """
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_by_id(self, transaction_id: int) -> Optional[InventoryTransaction]:
        """
        Get transaction by ID.

        Args:
            transaction_id: Transaction ID

        Returns:
            Transaction or None if not found
        """
        return self.db.query(InventoryTransaction).filter(
            InventoryTransaction.id == transaction_id
        ).first()

    def get_by_material(
        self,
        material_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionType] = None,
        limit: int = 100
    ) -> List[InventoryTransaction]:
        """
        Get transactions for a material with optional filters.

        Args:
            material_id: Material ID
            start_date: Filter by date >= start_date
            end_date: Filter by date <= end_date
            transaction_type: Filter by transaction type
            limit: Maximum records to return

        Returns:
            List of transactions ordered by date descending
        """
        query = self.db.query(InventoryTransaction).filter(
            InventoryTransaction.material_id == material_id
        )

        if start_date:
            query = query.filter(InventoryTransaction.transaction_date >= start_date)

        if end_date:
            query = query.filter(InventoryTransaction.transaction_date <= end_date)

        if transaction_type:
            query = query.filter(InventoryTransaction.transaction_type == transaction_type)

        return query.order_by(
            desc(InventoryTransaction.transaction_date)
        ).limit(limit).all()

    def get_by_reference(
        self,
        transaction_reference: str,
        transaction_type: Optional[TransactionType] = None
    ) -> List[InventoryTransaction]:
        """
        Get transactions by reference (e.g., work order number, PO number).

        Args:
            transaction_reference: Reference number (WO, PO, etc.)
            transaction_type: Optional filter by type

        Returns:
            List of transactions matching reference
        """
        query = self.db.query(InventoryTransaction).filter(
            InventoryTransaction.transaction_reference == transaction_reference
        )

        if transaction_type:
            query = query.filter(InventoryTransaction.transaction_type == transaction_type)

        return query.order_by(
            desc(InventoryTransaction.transaction_date)
        ).all()

    def get_by_storage_location(
        self,
        storage_location_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[InventoryTransaction]:
        """
        Get transactions for a storage location.

        Args:
            storage_location_id: Storage location ID
            start_date: Filter by date >= start_date
            end_date: Filter by date <= end_date
            limit: Maximum records to return

        Returns:
            List of transactions ordered by date descending
        """
        query = self.db.query(InventoryTransaction).filter(
            InventoryTransaction.storage_location_id == storage_location_id
        )

        if start_date:
            query = query.filter(InventoryTransaction.transaction_date >= start_date)

        if end_date:
            query = query.filter(InventoryTransaction.transaction_date <= end_date)

        return query.order_by(
            desc(InventoryTransaction.transaction_date)
        ).limit(limit).all()

    def get_receipts_by_material(
        self,
        material_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[InventoryTransaction]:
        """
        Get all goods receipts for a material (for FIFO costing).

        Args:
            material_id: Material ID
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of GOODS_RECEIPT transactions
        """
        return self.get_by_material(
            material_id=material_id,
            start_date=start_date,
            end_date=end_date,
            transaction_type=TransactionType.GOODS_RECEIPT
        )

    def get_issues_by_material(
        self,
        material_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[InventoryTransaction]:
        """
        Get all goods issues for a material.

        Args:
            material_id: Material ID
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of GOODS_ISSUE transactions
        """
        return self.get_by_material(
            material_id=material_id,
            start_date=start_date,
            end_date=end_date,
            transaction_type=TransactionType.GOODS_ISSUE
        )


class InventoryRepository:
    """
    Repository for Inventory entity.

    Provides CRUD and query methods for inventory records.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_material_and_location(
        self,
        material_id: int,
        storage_location_id: int,
        batch_number: str
    ) -> Optional['Inventory']:
        """
        Get inventory record for specific material, location, and batch.

        Args:
            material_id: Material ID
            storage_location_id: Storage location ID
            batch_number: Batch number

        Returns:
            Inventory record or None
        """
        from app.models.inventory import Inventory
        return self.db.query(Inventory).filter(
            and_(
                Inventory.material_id == material_id,
                Inventory.storage_location_id == storage_location_id,
                Inventory.batch_number == batch_number
            )
        ).first()

    def get_by_material(self, material_id: int) -> List['Inventory']:
        """
        Get all inventory records for a material (across all locations/batches).

        Args:
            material_id: Material ID

        Returns:
            List of inventory records
        """
        from app.models.inventory import Inventory
        return self.db.query(Inventory).filter(
            Inventory.material_id == material_id
        ).all()

    def create_or_update(
        self,
        organization_id: int,
        plant_id: int,
        material_id: int,
        storage_location_id: int,
        batch_number: str,
        quantity_change: float,
        unit_of_measure_id: int
    ) -> 'Inventory':
        """
        Create or update inventory record.

        If record exists, update quantity. Otherwise, create new record.

        Args:
            organization_id: Organization ID
            plant_id: Plant ID
            material_id: Material ID
            storage_location_id: Storage location ID
            batch_number: Batch number
            quantity_change: Quantity to add (positive) or subtract (negative)
            unit_of_measure_id: Unit of measure ID

        Returns:
            Updated or created inventory record
        """
        from app.models.inventory import Inventory

        # Try to find existing record
        inventory = self.get_by_material_and_location(
            material_id, storage_location_id, batch_number
        )

        if inventory:
            # Update existing
            inventory.quantity_on_hand += quantity_change
            inventory.last_movement_date = datetime.now()
        else:
            # Create new
            inventory = Inventory(
                organization_id=organization_id,
                plant_id=plant_id,
                material_id=material_id,
                storage_location_id=storage_location_id,
                batch_number=batch_number,
                quantity_on_hand=quantity_change,
                quantity_reserved=0.0,
                unit_of_measure_id=unit_of_measure_id,
                last_movement_date=datetime.now()
            )
            self.db.add(inventory)

        self.db.commit()
        self.db.refresh(inventory)
        return inventory
