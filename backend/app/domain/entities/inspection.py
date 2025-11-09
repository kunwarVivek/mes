"""
Domain entities for Quality Management - Inspection Plans and Logs.
Pure Python classes representing inspection business domain concepts.
"""
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass


class InspectionCharacteristic:
    """Value object for inspection characteristic"""

    def __init__(
        self,
        characteristic_name: str,
        target_value: float,
        lower_tolerance: float,
        upper_tolerance: float,
        measurement_unit: str
    ):
        self._characteristic_name = characteristic_name
        self._target_value = target_value
        self._lower_tolerance = lower_tolerance
        self._upper_tolerance = upper_tolerance
        self._measurement_unit = measurement_unit
        self._validate()

    def _validate(self):
        """Validate characteristic business rules"""
        if not self._characteristic_name:
            raise ValueError("Characteristic name cannot be empty")
        if self._lower_tolerance > self._upper_tolerance:
            raise ValueError("Lower tolerance cannot exceed upper tolerance")

    @property
    def characteristic_name(self) -> str:
        return self._characteristic_name

    @property
    def target_value(self) -> float:
        return self._target_value

    @property
    def lower_tolerance(self) -> float:
        return self._lower_tolerance

    @property
    def upper_tolerance(self) -> float:
        return self._upper_tolerance

    @property
    def measurement_unit(self) -> str:
        return self._measurement_unit

    def is_within_tolerance(self, measured_value: float) -> bool:
        """Check if measured value is within tolerance"""
        return self._lower_tolerance <= measured_value <= self._upper_tolerance

    def __repr__(self):
        return f"<InspectionCharacteristic(name='{self._characteristic_name}', target={self._target_value})>"


class InspectionPlanDomain:
    """Domain entity for Inspection Plan"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        plan_name: str,
        material_id: int,
        inspection_frequency: str,
        sample_size: int,
        is_active: bool = True,
        characteristics: Optional[List[InspectionCharacteristic]] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._plan_name = plan_name
        self._material_id = material_id
        self._inspection_frequency = inspection_frequency
        self._sample_size = sample_size
        self._is_active = is_active
        self._characteristics = characteristics or []
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate inspection plan business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if not self._plan_name:
            raise ValueError("Plan name cannot be empty")
        if self._material_id <= 0:
            raise ValueError("Material ID must be positive")
        if self._sample_size <= 0:
            raise ValueError("Sample size must be positive")
        if self._inspection_frequency not in ["PER_LOT", "PER_SHIFT", "HOURLY", "CONTINUOUS"]:
            raise ValueError("Invalid inspection frequency")

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
    def plan_name(self) -> str:
        return self._plan_name

    @property
    def material_id(self) -> int:
        return self._material_id

    @property
    def inspection_frequency(self) -> str:
        return self._inspection_frequency

    @property
    def sample_size(self) -> int:
        return self._sample_size

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def characteristics(self) -> List[InspectionCharacteristic]:
        return self._characteristics

    def add_characteristic(self, characteristic: InspectionCharacteristic) -> None:
        """Business logic: Add inspection characteristic"""
        if not isinstance(characteristic, InspectionCharacteristic):
            raise ValueError("Must be an InspectionCharacteristic instance")
        self._characteristics.append(characteristic)

    def activate(self) -> None:
        """Business logic: Activate inspection plan"""
        self._is_active = True

    def deactivate(self) -> None:
        """Business logic: Deactivate inspection plan"""
        self._is_active = False

    def __repr__(self):
        return f"<InspectionPlan(name='{self._plan_name}', material_id={self._material_id})>"


class InspectionLogDomain:
    """Domain entity for Inspection Log"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        inspection_plan_id: int,
        work_order_id: int,
        inspected_quantity: int,
        passed_quantity: int,
        failed_quantity: int,
        inspector_user_id: int,
        inspection_notes: Optional[str] = None,
        inspected_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._inspection_plan_id = inspection_plan_id
        self._work_order_id = work_order_id
        self._inspected_quantity = inspected_quantity
        self._passed_quantity = passed_quantity
        self._failed_quantity = failed_quantity
        self._inspector_user_id = inspector_user_id
        self._inspection_notes = inspection_notes
        self._inspected_at = inspected_at or datetime.utcnow()
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate inspection log business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if self._inspection_plan_id <= 0:
            raise ValueError("Inspection plan ID must be positive")
        if self._work_order_id <= 0:
            raise ValueError("Work order ID must be positive")
        if self._inspected_quantity <= 0:
            raise ValueError("Inspected quantity must be positive")
        if self._passed_quantity < 0:
            raise ValueError("Passed quantity cannot be negative")
        if self._failed_quantity < 0:
            raise ValueError("Failed quantity cannot be negative")
        if self._passed_quantity + self._failed_quantity != self._inspected_quantity:
            raise ValueError("Passed + Failed must equal Inspected quantity")

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
    def inspection_plan_id(self) -> int:
        return self._inspection_plan_id

    @property
    def work_order_id(self) -> int:
        return self._work_order_id

    @property
    def inspected_quantity(self) -> int:
        return self._inspected_quantity

    @property
    def passed_quantity(self) -> int:
        return self._passed_quantity

    @property
    def failed_quantity(self) -> int:
        return self._failed_quantity

    @property
    def inspector_user_id(self) -> int:
        return self._inspector_user_id

    def calculate_pass_rate(self) -> float:
        """Calculate inspection pass rate"""
        if self._inspected_quantity == 0:
            return 0.0
        return self._passed_quantity / self._inspected_quantity

    def __repr__(self):
        return f"<InspectionLog(plan_id={self._inspection_plan_id}, wo_id={self._work_order_id}, inspected={self._inspected_quantity})>"


class FPYCalculator:
    """First Pass Yield (FPY) calculation service"""

    @staticmethod
    def calculate_fpy(total_inspected: int, total_passed: int) -> float:
        """
        Calculate First Pass Yield (FPY).

        FPY = (Total Passed) / (Total Inspected)

        Args:
            total_inspected: Total number of units inspected
            total_passed: Total number of units passed on first inspection

        Returns:
            FPY as a decimal (0.0 to 1.0)

        Raises:
            ValueError: If inputs are invalid
        """
        if total_inspected <= 0:
            raise ValueError("Total inspected must be positive")
        if total_passed < 0:
            raise ValueError("Total passed cannot be negative")
        if total_passed > total_inspected:
            raise ValueError("Total passed cannot exceed total inspected")

        return total_passed / total_inspected

    @staticmethod
    def calculate_rolling_fpy(inspection_logs: List[InspectionLogDomain]) -> float:
        """
        Calculate rolling FPY across multiple inspection logs.

        Args:
            inspection_logs: List of inspection log domain entities

        Returns:
            Aggregate FPY as a decimal
        """
        if not inspection_logs:
            return 0.0

        total_inspected = sum(log.inspected_quantity for log in inspection_logs)
        total_passed = sum(log.passed_quantity for log in inspection_logs)

        if total_inspected == 0:
            return 0.0

        return total_passed / total_inspected
