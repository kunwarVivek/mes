"""
Production Log Domain Entity.

Represents real-time production tracking with business logic.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any


@dataclass
class ProductionLogDomain:
    """
    Production Log entity - Real-time production tracking.

    Tracks production output, scrap, and rework with yield rate calculations.
    """
    id: int
    organization_id: int
    plant_id: int
    work_order_id: int
    operation_id: Optional[int]
    machine_id: Optional[int]
    timestamp: datetime
    quantity_produced: Decimal
    quantity_scrapped: Decimal
    quantity_reworked: Decimal
    operator_id: Optional[int]
    shift_id: Optional[int]
    notes: Optional[str]
    custom_metadata: Optional[Dict[str, Any]]

    def __post_init__(self):
        """Validate production log data"""
        if self.quantity_produced < 0:
            raise ValueError("quantity_produced cannot be negative")

        if self.quantity_scrapped < 0:
            raise ValueError("quantity_scrapped cannot be negative")

        if self.quantity_reworked < 0:
            raise ValueError("quantity_reworked cannot be negative")

    @property
    def total_quantity(self) -> Decimal:
        """Total quantity including scrap and rework"""
        return self.quantity_produced + self.quantity_scrapped + self.quantity_reworked

    @property
    def yield_rate(self) -> Decimal:
        """
        Calculate yield rate (good parts / total parts) as percentage.

        Returns:
            Decimal: Yield rate as percentage (0-100)
        """
        total = self.total_quantity
        if total == 0:
            return Decimal("0")
        return (self.quantity_produced / total) * 100
