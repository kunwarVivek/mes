"""
Domain entity for MRP Run.
Pure Python class representing Material Requirements Planning execution.
Phase 3: Production Planning Module - Component 4
"""
from datetime import datetime
from typing import Optional


class MRPRunDomain:
    """Domain entity for MRP Run with business logic"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        run_number: str,
        run_date: datetime,
        planning_horizon_start: datetime,
        planning_horizon_end: datetime,
        materials_processed: int,
        planned_orders_created: int,
        total_shortage_qty: float,
        status: str,
        created_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._run_number = run_number.upper().strip()
        self._run_date = run_date
        self._planning_horizon_start = planning_horizon_start
        self._planning_horizon_end = planning_horizon_end
        self._materials_processed = materials_processed
        self._planned_orders_created = planned_orders_created
        self._total_shortage_qty = total_shortage_qty
        self._status = status
        self._created_at = created_at or datetime.utcnow()
        self._completed_at = completed_at

        self._validate()

    def _validate(self):
        """Validate MRP run business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if not self._run_number:
            raise ValueError("Run number cannot be empty")
        if self._materials_processed < 0:
            raise ValueError("Materials processed cannot be negative")
        if self._planned_orders_created < 0:
            raise ValueError("Planned orders created cannot be negative")
        if self._total_shortage_qty < 0:
            raise ValueError("Total shortage quantity cannot be negative")
        if self._status not in ["RUNNING", "COMPLETED", "FAILED"]:
            raise ValueError("Invalid MRP run status")
        if self._planning_horizon_start > self._planning_horizon_end:
            raise ValueError("Planning horizon start must be before end")

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
    def run_number(self) -> str:
        return self._run_number

    @property
    def run_date(self) -> datetime:
        return self._run_date

    @property
    def planning_horizon_start(self) -> datetime:
        return self._planning_horizon_start

    @property
    def planning_horizon_end(self) -> datetime:
        return self._planning_horizon_end

    @property
    def materials_processed(self) -> int:
        return self._materials_processed

    @property
    def planned_orders_created(self) -> int:
        return self._planned_orders_created

    @property
    def total_shortage_qty(self) -> float:
        return self._total_shortage_qty

    @property
    def status(self) -> str:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def completed_at(self) -> Optional[datetime]:
        return self._completed_at

    def start(self) -> None:
        """Business logic: Start MRP run"""
        if self._status != "RUNNING":
            raise ValueError("MRP run must be in RUNNING status to start")

    def complete(self, materials_processed: int, planned_orders_created: int, total_shortage_qty: float) -> None:
        """Business logic: Complete MRP run (RUNNING -> COMPLETED)"""
        if self._status != "RUNNING":
            raise ValueError("MRP run can only be completed from RUNNING status")

        self._status = "COMPLETED"
        self._materials_processed = materials_processed
        self._planned_orders_created = planned_orders_created
        self._total_shortage_qty = total_shortage_qty
        self._completed_at = datetime.utcnow()

    def fail(self) -> None:
        """Business logic: Fail MRP run (RUNNING -> FAILED)"""
        if self._status != "RUNNING":
            raise ValueError("MRP run can only be failed from RUNNING status")

        self._status = "FAILED"
        self._completed_at = datetime.utcnow()

    def __repr__(self):
        return f"<MRPRun(run_number='{self._run_number}', status='{self._status}')>"
