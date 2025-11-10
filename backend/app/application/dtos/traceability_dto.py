"""
DTOs for Traceability (Lot/Batch, Serial Numbers, Genealogy)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from decimal import Decimal


# ========== Lot Batch DTOs ==========

class LotBatchCreateDTO(BaseModel):
    """DTO for creating a lot batch"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    plant_id: Optional[int] = Field(None, gt=0, description="Plant ID")
    lot_number: str = Field(..., min_length=1, max_length=100, description="Lot number")
    material_id: int = Field(..., gt=0, description="Material ID")
    supplier_lot_number: Optional[str] = Field(None, max_length=100, description="Supplier lot number")
    initial_quantity: Decimal = Field(..., gt=0, description="Initial quantity")
    unit_of_measure: Optional[str] = Field(None, max_length=50, description="Unit of measure")
    source_type: str = Field(..., description="Source type")
    source_reference_id: Optional[int] = Field(None, description="Source reference ID (WO/PO)")
    supplier_id: Optional[int] = Field(None, gt=0, description="Supplier ID")
    production_date: Optional[date] = Field(None, description="Production date")
    received_date: Optional[date] = Field(None, description="Received date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    retest_date: Optional[date] = Field(None, description="Retest date")
    warehouse_location: Optional[str] = Field(None, max_length=100, description="Warehouse location")
    bin_location: Optional[str] = Field(None, max_length=50, description="Bin location")
    traceability_attributes: Optional[Dict[str, Any]] = Field(None, description="Traceability attributes")
    custom_attributes: Optional[Dict[str, Any]] = Field(None, description="Custom attributes")
    notes: Optional[str] = Field(None, description="Notes")
    created_by: int = Field(..., gt=0, description="Created by user ID")

    @field_validator('source_type')
    @classmethod
    def validate_source_type(cls, v):
        valid_types = ['PURCHASED', 'MANUFACTURED', 'RETURNED', 'ADJUSTED', 'TRANSFERRED']
        if v not in valid_types:
            raise ValueError(f'source_type must be one of {valid_types}')
        return v


class LotBatchUpdateDTO(BaseModel):
    """DTO for updating a lot batch"""
    current_quantity: Optional[Decimal] = Field(None, ge=0)
    reserved_quantity: Optional[Decimal] = Field(None, ge=0)
    quality_status: Optional[str] = None
    inspection_status: Optional[str] = None
    certificate_number: Optional[str] = Field(None, max_length=100)
    warehouse_location: Optional[str] = Field(None, max_length=100)
    bin_location: Optional[str] = Field(None, max_length=50)
    traceability_attributes: Optional[Dict[str, Any]] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class LotBatchReserveDTO(BaseModel):
    """DTO for reserving quantity from a lot"""
    quantity: Decimal = Field(..., gt=0, description="Quantity to reserve")
    reserved_by: int = Field(..., gt=0, description="User ID reserving")
    reference_type: Optional[str] = Field(None, description="Reference type (e.g., WORK_ORDER)")
    reference_id: Optional[int] = Field(None, description="Reference ID")


class LotBatchConsumeDTO(BaseModel):
    """DTO for consuming quantity from a lot"""
    quantity: Decimal = Field(..., gt=0, description="Quantity to consume")
    consumed_by: int = Field(..., gt=0, description="User ID consuming")
    work_order_id: Optional[int] = Field(None, description="Work order ID")
    operation_sequence: Optional[int] = Field(None, description="Operation sequence")


class LotBatchResponse(BaseModel):
    """DTO for lot batch response"""
    id: int
    organization_id: int
    plant_id: Optional[int]
    lot_number: str
    material_id: int
    supplier_lot_number: Optional[str]
    initial_quantity: Decimal
    current_quantity: Decimal
    reserved_quantity: Decimal
    unit_of_measure: Optional[str]
    source_type: str
    source_reference_id: Optional[int]
    supplier_id: Optional[int]
    production_date: Optional[date]
    received_date: Optional[date]
    expiry_date: Optional[date]
    retest_date: Optional[date]
    quality_status: str
    inspection_status: Optional[str]
    certificate_number: Optional[str]
    warehouse_location: Optional[str]
    bin_location: Optional[str]
    traceability_attributes: Optional[Dict[str, Any]]
    custom_attributes: Optional[Dict[str, Any]]
    notes: Optional[str]
    is_active: bool
    is_depleted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int

    class Config:
        from_attributes = True


# ========== Serial Number DTOs ==========

class SerialNumberCreateDTO(BaseModel):
    """DTO for creating a serial number"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    plant_id: Optional[int] = Field(None, gt=0, description="Plant ID")
    serial_number: str = Field(..., min_length=1, max_length=100, description="Serial number")
    material_id: int = Field(..., gt=0, description="Material ID")
    lot_batch_id: Optional[int] = Field(None, gt=0, description="Lot batch ID")
    work_order_id: Optional[int] = Field(None, gt=0, description="Work order ID")
    production_date: Optional[date] = Field(None, description="Production date")
    production_line: Optional[str] = Field(None, max_length=100, description="Production line")
    warehouse_location: Optional[str] = Field(None, max_length=100, description="Warehouse location")
    traceability_attributes: Optional[Dict[str, Any]] = Field(None, description="Traceability attributes")
    custom_attributes: Optional[Dict[str, Any]] = Field(None, description="Custom attributes")
    notes: Optional[str] = Field(None, description="Notes")
    created_by: int = Field(..., gt=0, description="Created by user ID")


class SerialNumberUpdateDTO(BaseModel):
    """DTO for updating a serial number"""
    status: Optional[str] = None
    quality_status: Optional[str] = None
    current_location: Optional[str] = Field(None, max_length=200)
    warehouse_location: Optional[str] = Field(None, max_length=100)
    customer_id: Optional[int] = Field(None, gt=0)
    shipment_id: Optional[int] = Field(None, gt=0)
    shipped_date: Optional[date] = None
    installation_date: Optional[date] = None
    installation_location: Optional[str] = Field(None, max_length=200)
    warranty_start_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    last_service_date: Optional[date] = None
    traceability_attributes: Optional[Dict[str, Any]] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class SerialNumberShipDTO(BaseModel):
    """DTO for shipping a serial number"""
    customer_id: int = Field(..., gt=0, description="Customer ID")
    shipment_id: Optional[int] = Field(None, description="Shipment ID")
    shipped_date: date = Field(..., description="Shipped date")
    shipped_by: int = Field(..., gt=0, description="User ID")


class SerialNumberResponse(BaseModel):
    """DTO for serial number response"""
    id: int
    organization_id: int
    plant_id: Optional[int]
    serial_number: str
    material_id: int
    lot_batch_id: Optional[int]
    work_order_id: Optional[int]
    production_date: Optional[date]
    production_line: Optional[str]
    status: str
    quality_status: str
    current_location: Optional[str]
    warehouse_location: Optional[str]
    customer_id: Optional[int]
    shipment_id: Optional[int]
    shipped_date: Optional[date]
    installation_date: Optional[date]
    installation_location: Optional[str]
    warranty_start_date: Optional[date]
    warranty_end_date: Optional[date]
    last_service_date: Optional[date]
    traceability_attributes: Optional[Dict[str, Any]]
    custom_attributes: Optional[Dict[str, Any]]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int

    class Config:
        from_attributes = True


# ========== Traceability Link DTOs ==========

class TraceabilityLinkCreateDTO(BaseModel):
    """DTO for creating a traceability link"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    parent_type: str = Field(..., description="Parent type (LOT or SERIAL)")
    parent_lot_id: Optional[int] = Field(None, description="Parent lot ID")
    parent_serial_id: Optional[int] = Field(None, description="Parent serial ID")
    child_type: str = Field(..., description="Child type (LOT or SERIAL)")
    child_lot_id: Optional[int] = Field(None, description="Child lot ID")
    child_serial_id: Optional[int] = Field(None, description="Child serial ID")
    relationship_type: str = Field(..., description="Relationship type")
    quantity_used: Optional[Decimal] = Field(None, gt=0, description="Quantity used")
    unit_of_measure: Optional[str] = Field(None, max_length=50, description="Unit of measure")
    work_order_id: Optional[int] = Field(None, description="Work order ID")
    operation_sequence: Optional[int] = Field(None, description="Operation sequence")
    link_date: datetime = Field(..., description="Link date")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_by: int = Field(..., gt=0, description="Created by user ID")

    @field_validator('parent_type', 'child_type')
    @classmethod
    def validate_entity_type(cls, v):
        valid_types = ['LOT', 'SERIAL']
        if v not in valid_types:
            raise ValueError(f'type must be one of {valid_types}')
        return v

    @field_validator('relationship_type')
    @classmethod
    def validate_relationship_type(cls, v):
        valid_types = ['CONSUMED_IN', 'ASSEMBLED_INTO', 'PACKAGED_WITH', 'DERIVED_FROM', 'SPLIT_FROM', 'MERGED_INTO']
        if v not in valid_types:
            raise ValueError(f'relationship_type must be one of {valid_types}')
        return v


class TraceabilityLinkResponse(BaseModel):
    """DTO for traceability link response"""
    id: int
    organization_id: int
    parent_type: str
    parent_lot_id: Optional[int]
    parent_serial_id: Optional[int]
    child_type: str
    child_lot_id: Optional[int]
    child_serial_id: Optional[int]
    relationship_type: str
    quantity_used: Optional[Decimal]
    unit_of_measure: Optional[str]
    work_order_id: Optional[int]
    operation_sequence: Optional[int]
    link_date: datetime
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True


# ========== Genealogy DTOs ==========

class GenealogyRecordCreateDTO(BaseModel):
    """DTO for creating a genealogy record"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    entity_type: str = Field(..., description="Entity type (LOT or SERIAL)")
    entity_id: int = Field(..., gt=0, description="Entity ID")
    entity_identifier: str = Field(..., min_length=1, max_length=100, description="Lot number or serial number")
    operation_type: str = Field(..., description="Operation type")
    operation_timestamp: datetime = Field(..., description="Operation timestamp")
    work_order_id: Optional[int] = Field(None, description="Work order ID")
    reference_type: Optional[str] = Field(None, max_length=50, description="Reference type")
    reference_id: Optional[int] = Field(None, description="Reference ID")
    quantity_before: Optional[Decimal] = Field(None, description="Quantity before operation")
    quantity_after: Optional[Decimal] = Field(None, description="Quantity after operation")
    quantity_change: Optional[Decimal] = Field(None, description="Quantity change")
    status_before: Optional[str] = Field(None, max_length=50, description="Status before")
    status_after: Optional[str] = Field(None, max_length=50, description="Status after")
    location_before: Optional[str] = Field(None, max_length=200, description="Location before")
    location_after: Optional[str] = Field(None, max_length=200, description="Location after")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    performed_by: int = Field(..., gt=0, description="Performed by user ID")

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        valid_types = ['LOT', 'SERIAL']
        if v not in valid_types:
            raise ValueError(f'entity_type must be one of {valid_types}')
        return v


class GenealogyRecordResponse(BaseModel):
    """DTO for genealogy record response"""
    id: int
    organization_id: int
    entity_type: str
    entity_id: int
    entity_identifier: str
    operation_type: str
    operation_timestamp: datetime
    work_order_id: Optional[int]
    reference_type: Optional[str]
    reference_id: Optional[int]
    quantity_before: Optional[Decimal]
    quantity_after: Optional[Decimal]
    quantity_change: Optional[Decimal]
    status_before: Optional[str]
    status_after: Optional[str]
    location_before: Optional[str]
    location_after: Optional[str]
    metadata: Optional[Dict[str, Any]]
    performed_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# ========== Genealogy Query DTOs ==========

class GenealogyQueryRequest(BaseModel):
    """DTO for querying genealogy"""
    entity_type: str = Field(..., description="Entity type (LOT or SERIAL)")
    entity_identifier: str = Field(..., description="Lot number or serial number")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    operation_types: Optional[List[str]] = Field(None, description="Filter by operation types")


class WhereUsedRequest(BaseModel):
    """DTO for where-used query"""
    entity_type: str = Field(..., description="Entity type (LOT or SERIAL)")
    entity_id: int = Field(..., gt=0, description="Entity ID")
    max_depth: int = Field(default=5, ge=1, le=10, description="Maximum depth to traverse")


class WhereFromRequest(BaseModel):
    """DTO for where-from (reverse genealogy) query"""
    entity_type: str = Field(..., description="Entity type (LOT or SERIAL)")
    entity_id: int = Field(..., gt=0, description="Entity ID")
    max_depth: int = Field(default=5, ge=1, le=10, description="Maximum depth to traverse")


class GenealogyTreeNode(BaseModel):
    """Single node in genealogy tree"""
    entity_type: str
    entity_id: int
    entity_identifier: str
    material_id: Optional[int]
    quantity: Optional[Decimal]
    relationship_type: Optional[str]
    depth: int
    children: List['GenealogyTreeNode'] = []


class GenealogyTreeResponse(BaseModel):
    """DTO for genealogy tree response"""
    root: GenealogyTreeNode
    total_nodes: int
    max_depth_reached: int
