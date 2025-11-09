"""
SAP Data Transfer Objects (DTOs)
Models for SAP data exchange between Unison and SAP systems
"""
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional


class SAPMaterialDTO(BaseModel):
    """Material master data DTO for SAP sync"""

    material_number: str
    description: str
    base_uom: str
    category: str
    safety_stock: float = 0.0
    reorder_point: float = 0.0
    lot_size: float = 1.0
    lead_time_days: int = 0
    procurement_type: Optional[str] = None
    mrp_type: Optional[str] = None


class SAPInventoryTransactionDTO(BaseModel):
    """Inventory transaction DTO for SAP sync"""

    document_number: Optional[str] = None
    material_number: str
    plant: str
    storage_location: str
    batch: str
    quantity: Decimal
    base_uom: str
    movement_type: str
    posting_date: datetime
    reference_document: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    total_value: Optional[Decimal] = None


class SAPStandardCostDTO(BaseModel):
    """Standard cost DTO for SAP sync"""

    material_number: str
    plant: str
    standard_cost: Decimal
    currency: str
    valid_from: Optional[datetime] = None
    costing_type: Optional[str] = None


class SAPMovingAveragePriceDTO(BaseModel):
    """Moving average price DTO for SAP sync"""

    material_number: str
    plant: str
    moving_average_price: Decimal
    currency: str
    total_value: Decimal
    total_stock: Decimal


class SAPPriceChangeDTO(BaseModel):
    """Price change history DTO for SAP sync"""

    material_number: str
    plant: str
    change_date: datetime
    old_price: Decimal
    new_price: Decimal
    currency: str
    changed_by: str


class SAPCostUpdateDTO(BaseModel):
    """Cost update DTO for pushing to SAP"""

    material_number: str
    plant: str
    new_standard_cost: Decimal
    currency: str
    valid_from: datetime
    reason: Optional[str] = None
