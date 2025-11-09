"""
Domain entities for BOM (Bill of Materials) Management.
Pure Python classes representing business domain concepts.
"""
from datetime import datetime, date
from typing import Optional
import enum


class BOMType(str, enum.Enum):
    """Enum for BOM types"""
    PRODUCTION = "PRODUCTION"
    ENGINEERING = "ENGINEERING"
    PLANNING = "PLANNING"


class BOMNumber:
    """Value object for BOM number validation"""

    def __init__(self, value: str):
        self._value = value.upper().strip()
        self._validate()

    def _validate(self):
        """Validate BOM number format: max 50 chars"""
        if not self._value:
            raise ValueError("BOM number cannot be empty")
        if len(self._value) > 50:
            raise ValueError("BOM number cannot exceed 50 characters")

    @property
    def value(self) -> str:
        return self._value

    def __str__(self):
        return self._value

    def __repr__(self):
        return f"BOMNumber('{self._value}')"

    def __eq__(self, other):
        if isinstance(other, BOMNumber):
            return self._value == other._value
        return False


class BOMHeaderDomain:
    """Domain entity for BOM Header"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        bom_number: BOMNumber,
        material_id: int,
        bom_version: int,
        bom_name: str,
        bom_type: BOMType,
        base_quantity: float,
        unit_of_measure_id: int,
        effective_start_date: Optional[date],
        effective_end_date: Optional[date],
        is_active: bool,
        created_by_user_id: int,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._bom_number = bom_number
        self._material_id = material_id
        self._bom_version = bom_version
        self._bom_name = bom_name
        self._bom_type = bom_type
        self._base_quantity = base_quantity
        self._unit_of_measure_id = unit_of_measure_id
        self._effective_start_date = effective_start_date
        self._effective_end_date = effective_end_date
        self._is_active = is_active
        self._created_by_user_id = created_by_user_id
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate BOM header business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if self._base_quantity <= 0:
            raise ValueError("Base quantity must be positive")
        if self._bom_version < 1:
            raise ValueError("BOM version must be at least 1")
        # Validate effectivity dates if both are present
        if (self._effective_start_date is not None and
            self._effective_end_date is not None and
            self._effective_start_date > self._effective_end_date):
            raise ValueError("Effective start date must be before or equal to effective end date")

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
    def bom_number(self) -> BOMNumber:
        return self._bom_number

    @property
    def material_id(self) -> int:
        return self._material_id

    @property
    def bom_version(self) -> int:
        return self._bom_version

    @property
    def bom_name(self) -> str:
        return self._bom_name

    @property
    def bom_type(self) -> BOMType:
        return self._bom_type

    @property
    def base_quantity(self) -> float:
        return self._base_quantity

    @property
    def unit_of_measure_id(self) -> int:
        return self._unit_of_measure_id

    @property
    def effective_start_date(self) -> Optional[date]:
        return self._effective_start_date

    @property
    def effective_end_date(self) -> Optional[date]:
        return self._effective_end_date

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def created_by_user_id(self) -> int:
        return self._created_by_user_id

    def activate(self) -> None:
        """Business logic: Activate BOM header"""
        self._is_active = True

    def deactivate(self) -> None:
        """Business logic: Deactivate BOM header"""
        self._is_active = False

    def create_new_version(
        self,
        new_effective_start: Optional[date],
        new_effective_end: Optional[date]
    ) -> 'BOMHeaderDomain':
        """Business logic: Create new version of BOM"""
        return BOMHeaderDomain(
            id=None,  # New entity, not yet persisted
            organization_id=self._organization_id,
            plant_id=self._plant_id,
            bom_number=self._bom_number,
            material_id=self._material_id,
            bom_version=self._bom_version + 1,
            bom_name=self._bom_name,
            bom_type=self._bom_type,
            base_quantity=self._base_quantity,
            unit_of_measure_id=self._unit_of_measure_id,
            effective_start_date=new_effective_start,
            effective_end_date=new_effective_end,
            is_active=False,  # New version starts inactive
            created_by_user_id=self._created_by_user_id
        )

    def __repr__(self):
        return f"<BOMHeader(bom_number='{self._bom_number}', version={self._bom_version}, material_id={self._material_id})>"


class BOMLineDomain:
    """Domain entity for BOM Line"""

    def __init__(
        self,
        id: Optional[int],
        bom_header_id: int,
        line_number: int,
        component_material_id: int,
        quantity: float,
        unit_of_measure_id: int,
        scrap_factor: float,
        operation_number: Optional[int],
        is_phantom: bool,
        backflush: bool,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._bom_header_id = bom_header_id
        self._line_number = line_number
        self._component_material_id = component_material_id
        self._quantity = quantity
        self._unit_of_measure_id = unit_of_measure_id
        self._scrap_factor = scrap_factor
        self._operation_number = operation_number
        self._is_phantom = is_phantom
        self._backflush = backflush
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate BOM line business rules"""
        if self._quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self._scrap_factor < 0 or self._scrap_factor > 100:
            raise ValueError("Scrap factor must be between 0 and 100")
        if self._line_number <= 0:
            raise ValueError("Line number must be positive")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def bom_header_id(self) -> int:
        return self._bom_header_id

    @property
    def line_number(self) -> int:
        return self._line_number

    @property
    def component_material_id(self) -> int:
        return self._component_material_id

    @property
    def quantity(self) -> float:
        return self._quantity

    @property
    def unit_of_measure_id(self) -> int:
        return self._unit_of_measure_id

    @property
    def scrap_factor(self) -> float:
        return self._scrap_factor

    @property
    def operation_number(self) -> Optional[int]:
        return self._operation_number

    @property
    def is_phantom(self) -> bool:
        return self._is_phantom

    @property
    def backflush(self) -> bool:
        return self._backflush

    def calculate_net_quantity_with_scrap(self) -> float:
        """Business logic: Calculate net quantity including scrap factor"""
        return self._quantity * (1 + self._scrap_factor / 100)

    def __repr__(self):
        return f"<BOMLine(bom_header_id={self._bom_header_id}, line_num={self._line_number}, component_mat_id={self._component_material_id})>"
