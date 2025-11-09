"""
Domain entity for Planned Order.
Pure Python class representing future production/purchase orders from MRP.
Phase 3: Production Planning Module - Component 4
"""
from datetime import datetime
from typing import Optional


class PlannedOrderDomain:
    """Domain entity for Planned Order with business logic"""

    def __init__(
        self,
        id: Optional[int],
        mrp_run_id: int,
        material_id: int,
        order_type: str,
        planned_quantity: float,
        unit_of_measure_id: int,
        need_date: datetime,
        order_date: datetime,
        source: str,
        status: str,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        converted_to_order_id: Optional[int] = None
    ):
        self._id = id
        self._mrp_run_id = mrp_run_id
        self._material_id = material_id
        self._order_type = order_type
        self._planned_quantity = planned_quantity
        self._unit_of_measure_id = unit_of_measure_id
        self._need_date = need_date
        self._order_date = order_date
        self._source = source
        self._status = status
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at
        self._converted_to_order_id = converted_to_order_id

        self._validate()

    def _validate(self):
        """Validate planned order business rules"""
        if self._mrp_run_id <= 0:
            raise ValueError("MRP run ID must be positive")
        if self._material_id <= 0:
            raise ValueError("Material ID must be positive")
        if self._planned_quantity <= 0:
            raise ValueError("Planned quantity must be positive")
        if self._unit_of_measure_id <= 0:
            raise ValueError("Unit of measure ID must be positive")
        if self._order_type not in ["PURCHASE", "PRODUCTION"]:
            raise ValueError("Invalid order type")
        if self._source not in ["MRP", "MANUAL"]:
            raise ValueError("Invalid source")
        if self._status not in ["PLANNED", "FIRMED", "CONVERTED"]:
            raise ValueError("Invalid status")
        if self._order_date > self._need_date:
            raise ValueError("Order date cannot be after need date")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def mrp_run_id(self) -> int:
        return self._mrp_run_id

    @property
    def material_id(self) -> int:
        return self._material_id

    @property
    def order_type(self) -> str:
        return self._order_type

    @property
    def planned_quantity(self) -> float:
        return self._planned_quantity

    @property
    def unit_of_measure_id(self) -> int:
        return self._unit_of_measure_id

    @property
    def need_date(self) -> datetime:
        return self._need_date

    @property
    def order_date(self) -> datetime:
        return self._order_date

    @property
    def source(self) -> str:
        return self._source

    @property
    def status(self) -> str:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    @property
    def converted_to_order_id(self) -> Optional[int]:
        return self._converted_to_order_id

    def firm(self) -> None:
        """Business logic: Firm planned order (PLANNED -> FIRMED)"""
        if self._status != "PLANNED":
            raise ValueError("Only PLANNED orders can be firmed")

        self._status = "FIRMED"
        self._updated_at = datetime.utcnow()

    def convert_to_work_order(self) -> None:
        """Business logic: Convert to work order (FIRMED -> CONVERTED)"""
        if self._status != "FIRMED":
            raise ValueError("Only FIRMED orders can be converted")
        if self._order_type != "PRODUCTION":
            raise ValueError("Only PRODUCTION orders can be converted to work orders")

        self._status = "CONVERTED"
        self._converted_to_order_id = 1  # Placeholder for actual work order ID
        self._updated_at = datetime.utcnow()

    def convert_to_purchase_order(self) -> None:
        """Business logic: Convert to purchase order (FIRMED -> CONVERTED)"""
        if self._status != "FIRMED":
            raise ValueError("Only FIRMED orders can be converted")
        if self._order_type != "PURCHASE":
            raise ValueError("Only PURCHASE orders can be converted to purchase orders")

        self._status = "CONVERTED"
        self._converted_to_order_id = 1  # Placeholder for actual purchase order ID
        self._updated_at = datetime.utcnow()

    def __repr__(self):
        return f"<PlannedOrder(material_id={self._material_id}, type='{self._order_type}', status='{self._status}')>"
