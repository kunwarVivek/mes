"""
Domain entity for Rework Order with business logic.
Extends Work Order to support rework operations.
Phase 3: Production Planning Module - Rework Order Extension
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from app.domain.entities.work_order import WorkOrderDomain


class ReworkMode(str, Enum):
    """Enum for rework operation modes"""
    CONSUME_ADDITIONAL_MATERIALS = "CONSUME_ADDITIONAL_MATERIALS"
    REPROCESS_EXISTING_WIP = "REPROCESS_EXISTING_WIP"
    HYBRID = "HYBRID"


class ReworkOrderDomain(WorkOrderDomain):
    """Domain entity for Rework Order with extended business logic"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        work_order_number: str,
        material_id: int,
        order_type: str,
        order_status: str,
        planned_quantity: float,
        actual_quantity: float,
        start_date_planned: Optional[datetime],
        end_date_planned: Optional[datetime],
        priority: int,
        created_by_user_id: int,
        is_rework_order: bool = False,
        parent_work_order_id: Optional[int] = None,
        rework_reason_code: Optional[str] = None,
        rework_mode: Optional[ReworkMode] = None,
        start_date_actual: Optional[datetime] = None,
        end_date_actual: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        # Initialize parent WorkOrder
        super().__init__(
            id=id,
            organization_id=organization_id,
            plant_id=plant_id,
            work_order_number=work_order_number,
            material_id=material_id,
            order_type=order_type,
            order_status=order_status,
            planned_quantity=planned_quantity,
            actual_quantity=actual_quantity,
            start_date_planned=start_date_planned,
            end_date_planned=end_date_planned,
            priority=priority,
            created_by_user_id=created_by_user_id,
            start_date_actual=start_date_actual,
            end_date_actual=end_date_actual,
            created_at=created_at
        )

        # Rework-specific attributes
        self._is_rework_order = is_rework_order
        self._parent_work_order_id = parent_work_order_id
        self._rework_reason_code = rework_reason_code
        self._rework_mode = rework_mode

        # Validate rework-specific business rules
        self._validate_rework_rules()

    def _validate_rework_rules(self):
        """Validate rework order specific business rules"""
        if self._is_rework_order:
            # Rework order must have parent work order
            if self._parent_work_order_id is None:
                raise ValueError("Rework order must have a parent work order")

            # Rework order must have reason code
            if not self._rework_reason_code:
                raise ValueError("Rework order must have a reason code")

            # Rework order must have rework mode
            if self._rework_mode is None:
                raise ValueError("Rework order must have a rework mode")

            # Rework order must have order_type REWORK
            if self._order_type != "REWORK":
                raise ValueError("Rework order must have order_type REWORK")
        else:
            # Non-rework orders cannot have parent work order
            if self._parent_work_order_id is not None:
                raise ValueError("Only rework orders can have a parent work order")

    @property
    def is_rework_order(self) -> bool:
        """Returns whether this is a rework order"""
        return self._is_rework_order

    @property
    def parent_work_order_id(self) -> Optional[int]:
        """Returns parent work order ID"""
        return self._parent_work_order_id

    @property
    def rework_reason_code(self) -> Optional[str]:
        """Returns rework reason code"""
        return self._rework_reason_code

    @property
    def rework_mode(self) -> Optional[ReworkMode]:
        """Returns rework mode"""
        return self._rework_mode

    def get_rework_cycle_number(self) -> int:
        """
        Get rework cycle number from parent chain.
        First rework = cycle 1, second rework = cycle 2, etc.
        """
        # For now, return 1 (first rework cycle)
        # In a full implementation, would traverse parent chain
        return 1

    def requires_material_consumption(self) -> bool:
        """
        Determine if this rework mode requires additional material consumption.

        Returns:
            True if mode requires materials (CONSUME_ADDITIONAL or HYBRID)
            False if mode reprocesses existing WIP only
        """
        if self._rework_mode == ReworkMode.REPROCESS_EXISTING_WIP:
            return False
        return True  # CONSUME_ADDITIONAL_MATERIALS or HYBRID

    def __repr__(self):
        if self._is_rework_order:
            return f"<ReworkOrder(number='{self._work_order_number}', mode='{self._rework_mode}', parent={self._parent_work_order_id})>"
        return super().__repr__()
