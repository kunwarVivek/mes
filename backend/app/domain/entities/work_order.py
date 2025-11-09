"""
Domain entities for Work Order Production Planning.
Pure Python classes representing business domain concepts.
Phase 3: Production Planning Module
"""
from datetime import datetime
from typing import Optional


class WorkCenterDomain:
    """Domain entity for Work Center"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        work_center_code: str,
        work_center_name: str,
        work_center_type: str,
        capacity_per_hour: float,
        cost_per_hour: float,
        is_active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._work_center_code = work_center_code.upper().strip()
        self._work_center_name = work_center_name
        self._work_center_type = work_center_type
        self._capacity_per_hour = capacity_per_hour
        self._cost_per_hour = cost_per_hour
        self._is_active = is_active
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate work center business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if not self._work_center_code:
            raise ValueError("Work center code cannot be empty")
        if self._capacity_per_hour <= 0:
            raise ValueError("Capacity per hour must be positive")
        if self._cost_per_hour < 0:
            raise ValueError("Cost per hour cannot be negative")
        if self._work_center_type not in ["MACHINE", "ASSEMBLY", "PACKAGING", "QUALITY_CHECK"]:
            raise ValueError("Invalid work center type")

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
    def work_center_code(self) -> str:
        return self._work_center_code

    @property
    def work_center_name(self) -> str:
        return self._work_center_name

    @property
    def work_center_type(self) -> str:
        return self._work_center_type

    @property
    def capacity_per_hour(self) -> float:
        return self._capacity_per_hour

    @property
    def cost_per_hour(self) -> float:
        return self._cost_per_hour

    @property
    def is_active(self) -> bool:
        return self._is_active

    def activate(self) -> None:
        """Business logic: Activate work center"""
        self._is_active = True

    def deactivate(self) -> None:
        """Business logic: Deactivate work center"""
        self._is_active = False

    def __repr__(self):
        return f"<WorkCenter(code='{self._work_center_code}', type='{self._work_center_type}')>"


class WorkOrderDomain:
    """Domain entity for Work Order with business logic"""

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
        start_date_actual: Optional[datetime] = None,
        end_date_actual: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._work_order_number = work_order_number.upper().strip()
        self._material_id = material_id
        self._order_type = order_type
        self._order_status = order_status
        self._planned_quantity = planned_quantity
        self._actual_quantity = actual_quantity
        self._start_date_planned = start_date_planned
        self._end_date_planned = end_date_planned
        self._start_date_actual = start_date_actual
        self._end_date_actual = end_date_actual
        self._priority = priority
        self._created_by_user_id = created_by_user_id
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate work order business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if not self._work_order_number:
            raise ValueError("Work order number cannot be empty")
        if self._planned_quantity <= 0:
            raise ValueError("Planned quantity must be positive")
        if self._actual_quantity < 0:
            raise ValueError("Actual quantity cannot be negative")
        if self._actual_quantity > self._planned_quantity:
            raise ValueError("Actual quantity cannot exceed planned quantity")
        if self._priority < 1 or self._priority > 10:
            raise ValueError("Priority must be between 1 and 10")
        if self._order_type not in ["PRODUCTION", "REWORK", "ASSEMBLY"]:
            raise ValueError("Invalid order type")
        if self._order_status not in ["PLANNED", "RELEASED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]:
            raise ValueError("Invalid order status")
        if self._start_date_planned and self._end_date_planned:
            if self._start_date_planned > self._end_date_planned:
                raise ValueError("Start date must be before end date")

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
    def work_order_number(self) -> str:
        return self._work_order_number

    @property
    def material_id(self) -> int:
        return self._material_id

    @property
    def order_type(self) -> str:
        return self._order_type

    @property
    def order_status(self) -> str:
        return self._order_status

    @property
    def planned_quantity(self) -> float:
        return self._planned_quantity

    @property
    def actual_quantity(self) -> float:
        return self._actual_quantity

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def start_date_actual(self) -> Optional[datetime]:
        return self._start_date_actual

    @property
    def end_date_actual(self) -> Optional[datetime]:
        return self._end_date_actual

    def start(self) -> None:
        """Business logic: Start work order (RELEASED -> IN_PROGRESS)"""
        if self._order_status != "RELEASED":
            raise ValueError("Work order can only be started from RELEASED status")
        self._order_status = "IN_PROGRESS"
        self._start_date_actual = datetime.utcnow()

    def complete(self) -> None:
        """Business logic: Complete work order (IN_PROGRESS -> COMPLETED)"""
        if self._order_status != "IN_PROGRESS":
            raise ValueError("Work order can only be completed from IN_PROGRESS status")
        self._order_status = "COMPLETED"
        self._end_date_actual = datetime.utcnow()

    def cancel(self) -> None:
        """Business logic: Cancel work order"""
        if self._order_status == "COMPLETED":
            raise ValueError("Cannot cancel a completed work order")
        self._order_status = "CANCELLED"

    def update_actual_quantity(self, quantity: float) -> None:
        """Business logic: Update actual quantity produced"""
        if quantity < 0:
            raise ValueError("Actual quantity cannot be negative")
        if quantity > self._planned_quantity:
            raise ValueError("Actual quantity cannot exceed planned quantity")
        self._actual_quantity = quantity

    def __repr__(self):
        return f"<WorkOrder(number='{self._work_order_number}', status='{self._order_status}')>"


class WorkOrderOperationDomain:
    """Domain entity for Work Order Operation"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        work_order_id: int,
        operation_number: int,
        operation_name: str,
        work_center_id: int,
        setup_time_minutes: float,
        run_time_per_unit_minutes: float,
        status: str,
        actual_setup_time: Optional[float] = None,
        actual_run_time: Optional[float] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._work_order_id = work_order_id
        self._operation_number = operation_number
        self._operation_name = operation_name
        self._work_center_id = work_center_id
        self._setup_time_minutes = setup_time_minutes
        self._run_time_per_unit_minutes = run_time_per_unit_minutes
        self._status = status
        self._actual_setup_time = actual_setup_time
        self._actual_run_time = actual_run_time
        self._start_time = start_time
        self._end_time = end_time
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate operation business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if self._operation_number <= 0:
            raise ValueError("Operation number must be positive")
        if self._setup_time_minutes < 0:
            raise ValueError("Setup time cannot be negative")
        if self._run_time_per_unit_minutes < 0:
            raise ValueError("Run time per unit cannot be negative")
        if self._status not in ["PENDING", "IN_PROGRESS", "COMPLETED", "SKIPPED"]:
            raise ValueError("Invalid operation status")

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
    def work_order_id(self) -> int:
        return self._work_order_id

    @property
    def operation_number(self) -> int:
        return self._operation_number

    @property
    def operation_name(self) -> str:
        return self._operation_name

    @property
    def work_center_id(self) -> int:
        return self._work_center_id

    @property
    def setup_time_minutes(self) -> float:
        return self._setup_time_minutes

    @property
    def run_time_per_unit_minutes(self) -> float:
        return self._run_time_per_unit_minutes

    @property
    def status(self) -> str:
        return self._status

    def __repr__(self):
        return f"<WorkOrderOperation(wo_id={self._work_order_id}, op_num={self._operation_number})>"
