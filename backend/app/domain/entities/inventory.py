"""
Domain entities for Inventory Management.
Pure Python classes representing business domain concepts.
"""
from datetime import datetime
from typing import Optional


class StorageLocationDomain:
    """Domain entity for Storage Location"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        location_code: str,
        location_name: str,
        location_type: str,
        is_active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._location_code = location_code.upper().strip()
        self._location_name = location_name
        self._location_type = location_type
        self._is_active = is_active
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate storage location business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if not self._location_code:
            raise ValueError("Location code cannot be empty")
        if len(self._location_code) > 20:
            raise ValueError("Location code cannot exceed 20 characters")
        if self._location_type not in ["WAREHOUSE", "PRODUCTION", "QUALITY", "BLOCKED"]:
            raise ValueError("Invalid location type")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def organization_id(self) -> int:
        return self._organization_id

    @property
    def plant_id(self) -> int:
        return self._plant_id

    @property
    def location_code(self) -> str:
        return self._location_code

    @property
    def location_name(self) -> str:
        return self._location_name

    @property
    def location_type(self) -> str:
        return self._location_type

    @property
    def is_active(self) -> bool:
        return self._is_active

    def activate(self) -> None:
        """Business logic: Activate storage location"""
        self._is_active = True

    def deactivate(self) -> None:
        """Business logic: Deactivate storage location"""
        self._is_active = False

    def __repr__(self):
        return f"<StorageLocation(code='{self._location_code}', type='{self._location_type}')>"


class InventoryDomain:
    """Domain entity for Inventory tracking"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        material_id: int,
        storage_location_id: int,
        batch_number: str,
        quantity_on_hand: float,
        quantity_reserved: float,
        unit_of_measure_id: int,
        last_movement_date: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._material_id = material_id
        self._storage_location_id = storage_location_id
        self._batch_number = batch_number
        self._quantity_on_hand = quantity_on_hand
        self._quantity_reserved = quantity_reserved
        self._unit_of_measure_id = unit_of_measure_id
        self._last_movement_date = last_movement_date
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate inventory business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if self._material_id <= 0:
            raise ValueError("Material ID must be positive")
        if self._storage_location_id <= 0:
            raise ValueError("Storage location ID must be positive")
        if self._quantity_on_hand < 0:
            raise ValueError("Quantity on hand cannot be negative")
        if self._quantity_reserved < 0:
            raise ValueError("Quantity reserved cannot be negative")
        if self._quantity_reserved > self._quantity_on_hand:
            raise ValueError("Reserved quantity cannot exceed quantity on hand")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def organization_id(self) -> int:
        return self._organization_id

    @property
    def plant_id(self) -> int:
        return self._plant_id

    @property
    def material_id(self) -> int:
        return self._material_id

    @property
    def storage_location_id(self) -> int:
        return self._storage_location_id

    @property
    def batch_number(self) -> str:
        return self._batch_number

    @property
    def quantity_on_hand(self) -> float:
        return self._quantity_on_hand

    @property
    def quantity_reserved(self) -> float:
        return self._quantity_reserved

    @property
    def quantity_available(self) -> float:
        """Computed property: available = on_hand - reserved"""
        return self._quantity_on_hand - self._quantity_reserved

    @property
    def unit_of_measure_id(self) -> int:
        return self._unit_of_measure_id

    @property
    def last_movement_date(self) -> Optional[datetime]:
        return self._last_movement_date

    def reserve_quantity(self, quantity: float) -> None:
        """
        Business logic: Reserve quantity for production or sales orders.

        Args:
            quantity: Amount to reserve

        Raises:
            ValueError: If insufficient available quantity
        """
        if quantity <= 0:
            raise ValueError("Quantity to reserve must be positive")

        available = self.quantity_available
        if quantity > available:
            raise ValueError(
                f"Insufficient available quantity. Available: {available}, Requested: {quantity}"
            )
        self._quantity_reserved += quantity

    def release_reserved_quantity(self, quantity: float) -> None:
        """
        Business logic: Release previously reserved quantity.

        Args:
            quantity: Amount to release

        Raises:
            ValueError: If trying to release more than reserved
        """
        if quantity <= 0:
            raise ValueError("Quantity to release must be positive")

        if quantity > self._quantity_reserved:
            raise ValueError(
                f"Cannot release more than reserved. Reserved: {self._quantity_reserved}, Requested: {quantity}"
            )
        self._quantity_reserved -= quantity

    def update_quantity(self, new_quantity: float) -> None:
        """
        Business logic: Update quantity on hand.

        Args:
            new_quantity: New quantity on hand

        Raises:
            ValueError: If new quantity is negative or less than reserved
        """
        if new_quantity < 0:
            raise ValueError("Quantity on hand cannot be negative")
        if new_quantity < self._quantity_reserved:
            raise ValueError("Cannot set quantity on hand below reserved quantity")

        self._quantity_on_hand = new_quantity
        self._last_movement_date = datetime.utcnow()

    def adjust_quantity(self, adjustment: float) -> None:
        """
        Business logic: Adjust quantity by a delta (positive or negative).

        Args:
            adjustment: Delta to add (positive) or subtract (negative)

        Raises:
            ValueError: If adjustment would make quantity negative
        """
        new_quantity = self._quantity_on_hand + adjustment
        self.update_quantity(new_quantity)

    def __repr__(self):
        return f"<Inventory(material_id={self._material_id}, location={self._storage_location_id}, on_hand={self._quantity_on_hand}, reserved={self._quantity_reserved})>"


class InventoryTransactionDomain:
    """Domain entity for Inventory Transaction (immutable audit trail)"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        material_id: int,
        storage_location_id: int,
        transaction_type: str,
        transaction_reference: str,
        batch_number: str,
        quantity: float,
        unit_of_measure_id: int,
        unit_cost: float,
        total_value: float,
        transaction_date: datetime,
        posted_by_user_id: int,
        notes: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._material_id = material_id
        self._storage_location_id = storage_location_id
        self._transaction_type = transaction_type
        self._transaction_reference = transaction_reference
        self._batch_number = batch_number
        self._quantity = quantity
        self._unit_of_measure_id = unit_of_measure_id
        self._unit_cost = unit_cost
        self._total_value = total_value
        self._transaction_date = transaction_date
        self._posted_by_user_id = posted_by_user_id
        self._notes = notes
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate transaction business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if self._material_id <= 0:
            raise ValueError("Material ID must be positive")
        if self._storage_location_id <= 0:
            raise ValueError("Storage location ID must be positive")

        valid_types = ["GOODS_RECEIPT", "GOODS_ISSUE", "TRANSFER_IN", "TRANSFER_OUT", "ADJUSTMENT"]
        if self._transaction_type not in valid_types:
            raise ValueError(f"Invalid transaction type: {self._transaction_type}")

        # Validate quantity sign based on transaction type
        if self._transaction_type in ["GOODS_RECEIPT", "TRANSFER_IN"]:
            if self._quantity <= 0:
                raise ValueError(f"{self._transaction_type} must have positive quantity")
        elif self._transaction_type in ["GOODS_ISSUE", "TRANSFER_OUT"]:
            if self._quantity >= 0:
                raise ValueError(f"{self._transaction_type} must have negative quantity")

        if not self._transaction_reference:
            raise ValueError("Transaction reference cannot be empty")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def organization_id(self) -> int:
        return self._organization_id

    @property
    def plant_id(self) -> int:
        return self._plant_id

    @property
    def material_id(self) -> int:
        return self._material_id

    @property
    def storage_location_id(self) -> int:
        return self._storage_location_id

    @property
    def transaction_type(self) -> str:
        return self._transaction_type

    @property
    def transaction_reference(self) -> str:
        return self._transaction_reference

    @property
    def batch_number(self) -> str:
        return self._batch_number

    @property
    def quantity(self) -> float:
        return self._quantity

    @property
    def unit_of_measure_id(self) -> int:
        return self._unit_of_measure_id

    @property
    def unit_cost(self) -> float:
        return self._unit_cost

    @property
    def total_value(self) -> float:
        return self._total_value

    @property
    def transaction_date(self) -> datetime:
        return self._transaction_date

    @property
    def posted_by_user_id(self) -> int:
        return self._posted_by_user_id

    @property
    def notes(self) -> Optional[str]:
        return self._notes

    def __repr__(self):
        return f"<InventoryTransaction(type='{self._transaction_type}', material_id={self._material_id}, qty={self._quantity})>"
