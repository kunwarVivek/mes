"""
Pydantic schemas for Inventory API endpoints.

These schemas define request/response models for material transactions.
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum


class TransactionTypeEnum(str, Enum):
    """Transaction type enumeration."""
    GOODS_RECEIPT = "GOODS_RECEIPT"
    GOODS_ISSUE = "GOODS_ISSUE"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    ADJUSTMENT = "ADJUSTMENT"


class ReferenceTypeEnum(str, Enum):
    """Reference type enumeration."""
    WORK_ORDER = "WORK_ORDER"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    SALES_ORDER = "SALES_ORDER"
    TRANSFER = "TRANSFER"
    MAINTENANCE = "MAINTENANCE"
    ADJUSTMENT = "ADJUSTMENT"


# ============================================================================
# Request Schemas
# ============================================================================

class ReceiveMaterialRequest(BaseModel):
    """Request schema for material receipt (goods receipt)."""

    storage_location_id: int = Field(..., description="Storage location ID where material will be stored")
    quantity: Decimal = Field(..., gt=0, description="Quantity to receive (must be positive)")
    batch_number: str = Field(..., min_length=1, max_length=50, description="Batch/lot number")
    transaction_reference: str = Field(..., min_length=1, max_length=100, description="Reference (e.g., PO-12345)")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Unit cost (uses material standard cost if not provided)")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date (defaults to now)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "storage_location_id": 1,
                "quantity": 100.0,
                "batch_number": "BATCH-2024-001",
                "transaction_reference": "PO-12345",
                "unit_cost": 25.50,
                "transaction_date": "2024-11-10T10:30:00Z",
                "notes": "Received from supplier XYZ"
            }
        }


class IssueMaterialRequest(BaseModel):
    """Request schema for material issue (goods issue)."""

    storage_location_id: int = Field(..., description="Storage location ID to issue from")
    quantity: Decimal = Field(..., gt=0, description="Quantity to issue (must be positive)")
    batch_number: str = Field(..., min_length=1, max_length=50, description="Batch/lot number")
    transaction_reference: str = Field(..., min_length=1, max_length=100, description="Reference (e.g., WO-00123)")
    reference_type: ReferenceTypeEnum = Field(..., description="Reference type (WORK_ORDER, SALES_ORDER, etc.)")
    reference_id: Optional[int] = Field(None, description="Reference entity ID (e.g., work order ID)")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date (defaults to now)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "storage_location_id": 1,
                "quantity": 50.0,
                "batch_number": "BATCH-2024-001",
                "transaction_reference": "WO-00123",
                "reference_type": "WORK_ORDER",
                "reference_id": 456,
                "transaction_date": "2024-11-10T14:30:00Z",
                "notes": "Issued for production work order WO-00123"
            }
        }


class AdjustInventoryRequest(BaseModel):
    """Request schema for inventory adjustment (physical count correction)."""

    storage_location_id: int = Field(..., description="Storage location ID")
    batch_number: str = Field(..., min_length=1, max_length=50, description="Batch/lot number")
    target_quantity: Decimal = Field(..., ge=0, description="Target quantity after adjustment (must be non-negative)")
    reason: str = Field(..., min_length=1, max_length=100, description="Adjustment reason (PHYSICAL_COUNT, DAMAGE, etc.)")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date (defaults to now)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "storage_location_id": 1,
                "batch_number": "BATCH-2024-001",
                "target_quantity": 95.0,
                "reason": "PHYSICAL_COUNT",
                "transaction_date": "2024-11-10T16:00:00Z",
                "notes": "Annual physical count adjustment - 5 units damaged"
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class MaterialTransactionResponse(BaseModel):
    """Response schema for inventory transaction."""

    id: int
    organization_id: int
    plant_id: int
    material_id: int
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    storage_location_id: int
    storage_location_code: Optional[str] = None
    transaction_type: TransactionTypeEnum
    transaction_reference: str
    batch_number: str
    quantity: float
    unit_of_measure: Optional[str] = None
    unit_cost: float
    total_value: float
    transaction_date: datetime
    posted_by_user_id: int
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1234,
                "organization_id": 1,
                "plant_id": 10,
                "material_id": 567,
                "material_code": "MAT-001",
                "material_description": "Steel Plate 10mm",
                "storage_location_id": 1,
                "storage_location_code": "WH-01",
                "transaction_type": "GOODS_RECEIPT",
                "transaction_reference": "PO-12345",
                "batch_number": "BATCH-2024-001",
                "quantity": 100.0,
                "unit_of_measure": "EA",
                "unit_cost": 25.50,
                "total_value": 2550.00,
                "transaction_date": "2024-11-10T10:30:00Z",
                "posted_by_user_id": 42,
                "notes": "Received from supplier XYZ",
                "created_at": "2024-11-10T10:30:15Z"
            }
        }


class InventoryBalanceResponse(BaseModel):
    """Response schema for inventory balance."""

    id: int
    organization_id: int
    plant_id: int
    material_id: int
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    storage_location_id: int
    storage_location_code: Optional[str] = None
    batch_number: str
    quantity_on_hand: float
    quantity_reserved: float
    quantity_available: float
    unit_of_measure: Optional[str] = None
    last_movement_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionHistoryResponse(BaseModel):
    """Response schema for transaction history list."""

    material_id: int
    material_code: str
    material_description: str
    total_transactions: int
    transactions: List[MaterialTransactionResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "material_id": 567,
                "material_code": "MAT-001",
                "material_description": "Steel Plate 10mm",
                "total_transactions": 3,
                "transactions": [
                    # ... list of transactions
                ]
            }
        }


class InventorySummaryResponse(BaseModel):
    """Response schema for inventory summary."""

    material_id: int
    material_code: str
    material_description: str
    total_on_hand: float
    total_reserved: float
    total_available: float
    unit_of_measure: str
    locations_count: int
    batches_count: int
    last_movement_date: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "material_id": 567,
                "material_code": "MAT-001",
                "material_description": "Steel Plate 10mm",
                "total_on_hand": 250.0,
                "total_reserved": 50.0,
                "total_available": 200.0,
                "unit_of_measure": "EA",
                "locations_count": 2,
                "batches_count": 3,
                "last_movement_date": "2024-11-10T14:30:00Z"
            }
        }
