"""
Domain entities for Material Management.
Pure Python classes representing business domain concepts.
"""
from datetime import datetime
from typing import Optional
import re


class MaterialNumber:
    """Value object for material number validation"""

    PATTERN = re.compile(r'^[A-Z0-9]{1,10}$')

    def __init__(self, value: str):
        self._value = value.upper().strip()
        self._validate()

    def _validate(self):
        """Validate material number format: alphanumeric, max 10 chars"""
        if not self._value:
            raise ValueError("Material number cannot be empty")
        if len(self._value) > 10:
            raise ValueError("Material number cannot exceed 10 characters")
        if not self.PATTERN.match(self._value):
            raise ValueError("Material number must be alphanumeric")

    @property
    def value(self) -> str:
        return self._value

    def __str__(self):
        return self._value

    def __repr__(self):
        return f"MaterialNumber('{self._value}')"

    def __eq__(self, other):
        if isinstance(other, MaterialNumber):
            return self._value == other._value
        return False


class UnitOfMeasureDomain:
    """Domain entity for Unit of Measure"""

    def __init__(
        self,
        id: Optional[int],
        uom_code: str,
        uom_name: str,
        dimension: str,
        is_base_unit: bool,
        conversion_factor: float,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._uom_code = uom_code.upper().strip()
        self._uom_name = uom_name
        self._dimension = dimension
        self._is_base_unit = is_base_unit
        self._conversion_factor = conversion_factor
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate UOM business rules"""
        if not self._uom_code:
            raise ValueError("UOM code cannot be empty")
        if len(self._uom_code) > 10:
            raise ValueError("UOM code cannot exceed 10 characters")
        if self._conversion_factor <= 0:
            raise ValueError("Conversion factor must be positive")
        if self._is_base_unit and self._conversion_factor != 1.0:
            raise ValueError("Base unit must have conversion factor of 1.0")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def uom_code(self) -> str:
        return self._uom_code

    @property
    def uom_name(self) -> str:
        return self._uom_name

    @property
    def dimension(self) -> str:
        return self._dimension

    @property
    def is_base_unit(self) -> bool:
        return self._is_base_unit

    @property
    def conversion_factor(self) -> float:
        return self._conversion_factor

    def __repr__(self):
        return f"<UnitOfMeasure(code='{self._uom_code}', dimension='{self._dimension}')>"


class MaterialCategoryDomain:
    """Domain entity for Material Category"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        category_code: str,
        category_name: str,
        parent_category_id: Optional[int] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._category_code = category_code.upper().strip()
        self._category_name = category_name
        self._parent_category_id = parent_category_id
        self._is_active = is_active
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate category business rules"""
        if not self._category_code:
            raise ValueError("Category code cannot be empty")
        if len(self._category_code) > 20:
            raise ValueError("Category code cannot exceed 20 characters")
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def organization_id(self) -> int:
        return self._organization_id

    @property
    def category_code(self) -> str:
        return self._category_code

    @property
    def category_name(self) -> str:
        return self._category_name

    @property
    def parent_category_id(self) -> Optional[int]:
        return self._parent_category_id

    @property
    def is_active(self) -> bool:
        return self._is_active

    def activate(self) -> None:
        """Business logic: Activate category"""
        self._is_active = True

    def deactivate(self) -> None:
        """Business logic: Deactivate category"""
        self._is_active = False

    def __repr__(self):
        return f"<MaterialCategory(code='{self._category_code}', org={self._organization_id})>"


class MaterialDomain:
    """Domain entity for Material master data"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        material_number: MaterialNumber,
        material_name: str,
        description: str,
        material_category_id: int,
        base_uom_id: int,
        procurement_type: str,
        mrp_type: str,
        safety_stock: float,
        reorder_point: float,
        lot_size: float,
        lead_time_days: int,
        is_active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._material_number = material_number
        self._material_name = material_name
        self._description = description
        self._material_category_id = material_category_id
        self._base_uom_id = base_uom_id
        self._procurement_type = procurement_type
        self._mrp_type = mrp_type
        self._safety_stock = safety_stock
        self._reorder_point = reorder_point
        self._lot_size = lot_size
        self._lead_time_days = lead_time_days
        self._is_active = is_active
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate material business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if not self._material_name:
            raise ValueError("Material name cannot be empty")
        if self._safety_stock < 0:
            raise ValueError("Safety stock cannot be negative")
        if self._reorder_point < 0:
            raise ValueError("Reorder point cannot be negative")
        if self._lot_size <= 0:
            raise ValueError("Lot size must be positive")
        if self._lead_time_days < 0:
            raise ValueError("Lead time cannot be negative")
        if self._procurement_type not in ["PURCHASE", "MANUFACTURE", "BOTH"]:
            raise ValueError("Invalid procurement type")
        if self._mrp_type not in ["MRP", "REORDER"]:
            raise ValueError("Invalid MRP type")

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
    def material_number(self) -> MaterialNumber:
        return self._material_number

    @property
    def material_name(self) -> str:
        return self._material_name

    @property
    def safety_stock(self) -> float:
        return self._safety_stock

    @property
    def reorder_point(self) -> float:
        return self._reorder_point

    @property
    def lead_time_days(self) -> int:
        return self._lead_time_days

    @property
    def is_active(self) -> bool:
        return self._is_active

    def activate(self) -> None:
        """Business logic: Activate material"""
        self._is_active = True

    def deactivate(self) -> None:
        """Business logic: Deactivate material"""
        self._is_active = False

    def update_safety_stock(self, new_stock: float) -> None:
        """Business logic: Update safety stock level"""
        if new_stock < 0:
            raise ValueError("Safety stock cannot be negative")
        self._safety_stock = new_stock

    def update_reorder_point(self, new_point: float) -> None:
        """Business logic: Update reorder point"""
        if new_point < 0:
            raise ValueError("Reorder point cannot be negative")
        self._reorder_point = new_point

    def update_lead_time(self, new_days: int) -> None:
        """Business logic: Update lead time"""
        if new_days < 0:
            raise ValueError("Lead time cannot be negative")
        self._lead_time_days = new_days

    def __repr__(self):
        return f"<Material(number='{self._material_number}', org={self._organization_id}, plant={self._plant_id})>"
