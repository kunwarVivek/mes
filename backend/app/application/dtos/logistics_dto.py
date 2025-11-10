"""
Data Transfer Objects (DTOs) for Logistics Module API.

Pydantic v2 schemas for request/response validation.
Phase: Logistics & Shipment Tracking - Barcode/QR Integration
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.models.logistics import ShipmentType, ShipmentStatus, BarcodeType, ScanResolution


# ==================== Shipment DTOs ====================

class ShipmentCreateDTO(BaseModel):
    """DTO for creating a new shipment"""
    shipment_type: ShipmentType = Field(description="Type of shipment (INBOUND, OUTBOUND, TRANSFER, RETURN)")
    carrier_name: Optional[str] = Field(default=None, max_length=100, description="Carrier/shipping company name")
    tracking_number: Optional[str] = Field(default=None, max_length=100, description="Carrier tracking number")
    origin_location: Optional[str] = Field(default=None, max_length=200, description="Origin address/location")
    destination_location: Optional[str] = Field(default=None, max_length=200, description="Destination address/location")
    planned_ship_date: Optional[datetime] = Field(default=None, description="Planned shipment date")
    planned_delivery_date: Optional[datetime] = Field(default=None, description="Planned delivery date")
    weight_uom: str = Field(default="KG", max_length=10, description="Weight unit of measure (KG, LB, etc.)")
    volume_uom: str = Field(default="M3", max_length=10, description="Volume unit of measure (M3, FT3, etc.)")
    freight_cost: float = Field(default=0.0, ge=0, description="Freight/shipping cost")
    currency_code: str = Field(default="USD", max_length=3, description="Currency code (ISO 4217)")
    reference_document_type: Optional[str] = Field(default=None, max_length=50, description="Reference doc type (PO, WO, SO)")
    reference_document_id: Optional[int] = Field(default=None, gt=0, description="Reference document ID")
    notes: Optional[str] = Field(default=None, description="Additional notes")

    @field_validator('freight_cost')
    @classmethod
    def validate_freight_cost(cls, v: float) -> float:
        """Validate freight cost is non-negative"""
        if v < 0:
            raise ValueError('freight_cost must be non-negative')
        return v

    @model_validator(mode='after')
    def validate_dates(self):
        """Validate planned dates are logical"""
        if self.planned_ship_date and self.planned_delivery_date:
            if self.planned_delivery_date < self.planned_ship_date:
                raise ValueError('planned_delivery_date must be after planned_ship_date')
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "shipment_type": "OUTBOUND",
                "carrier_name": "FedEx",
                "tracking_number": "1234567890",
                "origin_location": "Plant A, 123 Main St, Chicago, IL",
                "destination_location": "Warehouse B, 456 Oak Ave, Dallas, TX",
                "planned_ship_date": "2025-11-10T08:00:00Z",
                "planned_delivery_date": "2025-11-12T17:00:00Z",
                "weight_uom": "KG",
                "volume_uom": "M3",
                "freight_cost": 250.00,
                "currency_code": "USD",
                "reference_document_type": "SO",
                "reference_document_id": 5001,
                "notes": "Fragile items - handle with care"
            }
        }
    )


class ShipmentUpdateDTO(BaseModel):
    """DTO for updating an existing shipment (partial updates)"""
    carrier_name: Optional[str] = Field(default=None, max_length=100)
    tracking_number: Optional[str] = Field(default=None, max_length=100)
    origin_location: Optional[str] = Field(default=None, max_length=200)
    destination_location: Optional[str] = Field(default=None, max_length=200)
    planned_ship_date: Optional[datetime] = None
    actual_ship_date: Optional[datetime] = None
    planned_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    total_weight: Optional[float] = Field(default=None, ge=0)
    total_volume: Optional[float] = Field(default=None, ge=0)
    freight_cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "actual_ship_date": "2025-11-10T09:30:00Z",
                "tracking_number": "1234567890",
                "notes": "Shipped on time"
            }
        }
    )


class ShipmentStatusUpdateDTO(BaseModel):
    """DTO for updating shipment status with transition validation"""
    new_status: ShipmentStatus = Field(description="New shipment status")
    status_notes: Optional[str] = Field(default=None, description="Notes about status change")
    timestamp: Optional[datetime] = Field(default=None, description="Status change timestamp (defaults to now)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_status": "IN_TRANSIT",
                "status_notes": "Shipment picked up by carrier",
                "timestamp": "2025-11-10T09:30:00Z"
            }
        }
    )


class ShipmentResponse(BaseModel):
    """DTO for shipment response"""
    id: int
    organization_id: int
    plant_id: int
    shipment_number: str
    shipment_type: str
    shipment_status: str
    carrier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    origin_location: Optional[str] = None
    destination_location: Optional[str] = None
    planned_ship_date: Optional[datetime] = None
    actual_ship_date: Optional[datetime] = None
    planned_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    total_weight: float
    weight_uom: str
    total_volume: float
    volume_uom: str
    freight_cost: float
    currency_code: str
    reference_document_type: Optional[str] = None
    reference_document_id: Optional[int] = None
    notes: Optional[str] = None
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List['ShipmentItemResponse'] = []
    is_overdue: bool = False
    calculated_total_weight: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# ==================== Shipment Item DTOs ====================

class ShipmentItemCreateDTO(BaseModel):
    """DTO for creating a shipment item"""
    line_number: int = Field(gt=0, description="Line number within shipment (must be positive)")
    material_id: Optional[int] = Field(default=None, gt=0, description="Material ID (if applicable)")
    material_description: Optional[str] = Field(default=None, max_length=200, description="Material description")
    quantity: float = Field(gt=0, description="Quantity (must be positive)")
    unit_of_measure_id: int = Field(gt=0, description="Unit of measure ID")
    batch_number: Optional[str] = Field(default=None, max_length=50, description="Batch/lot number")
    serial_number: Optional[str] = Field(default=None, max_length=50, description="Serial number")
    weight: Optional[float] = Field(default=None, ge=0, description="Item weight")
    weight_uom: Optional[str] = Field(default=None, max_length=10, description="Weight UOM")
    volume: Optional[float] = Field(default=None, ge=0, description="Item volume")
    volume_uom: Optional[str] = Field(default=None, max_length=10, description="Volume UOM")
    package_id: Optional[str] = Field(default=None, max_length=50, description="Package identifier")
    package_type: Optional[str] = Field(default=None, max_length=50, description="Package type (box, pallet, etc.)")

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        """Validate quantity is positive"""
        if v <= 0:
            raise ValueError('quantity must be positive')
        return v

    @field_validator('line_number')
    @classmethod
    def validate_line_number(cls, v: int) -> int:
        """Validate line number is positive"""
        if v <= 0:
            raise ValueError('line_number must be positive')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "line_number": 10,
                "material_id": 1001,
                "material_description": "Steel Plate - 1/4 inch",
                "quantity": 50.0,
                "unit_of_measure_id": 1,
                "batch_number": "BATCH-2025-001",
                "weight": 125.5,
                "weight_uom": "KG",
                "package_id": "PKG-001",
                "package_type": "PALLET"
            }
        }
    )


class ShipmentItemResponse(BaseModel):
    """DTO for shipment item response"""
    id: int
    organization_id: int
    plant_id: int
    shipment_id: int
    line_number: int
    material_id: Optional[int] = None
    material_description: Optional[str] = None
    quantity: float
    unit_of_measure_id: int
    batch_number: Optional[str] = None
    serial_number: Optional[str] = None
    weight: Optional[float] = None
    weight_uom: Optional[str] = None
    volume: Optional[float] = None
    volume_uom: Optional[str] = None
    package_id: Optional[str] = None
    package_type: Optional[str] = None
    barcode_value: Optional[str] = None
    barcode_type: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Barcode Label DTOs ====================

class BarcodeLabelCreateDTO(BaseModel):
    """DTO for creating a barcode label"""
    barcode_value: str = Field(max_length=100, description="Barcode/QR code value")
    barcode_type: BarcodeType = Field(description="Type of barcode (CODE128, QR_CODE, etc.)")
    entity_type: str = Field(max_length=50, description="Entity type (shipment_item, material, etc.)")
    entity_id: int = Field(gt=0, description="Entity ID")
    shipment_item_id: Optional[int] = Field(default=None, gt=0, description="Shipment item ID (if applicable)")
    label_format: str = Field(default="PDF", max_length=50, description="Label format (PDF, PNG, ZPL)")
    label_size: str = Field(default="4x6", max_length=20, description="Label size (4x6, 2x3, etc.)")
    label_data: Optional[str] = Field(default=None, description="Additional label data (JSON)")
    expires_at: Optional[datetime] = Field(default=None, description="Label expiration date")

    @field_validator('entity_id')
    @classmethod
    def validate_entity_id(cls, v: int) -> int:
        """Validate entity ID is positive"""
        if v <= 0:
            raise ValueError('entity_id must be positive')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "barcode_value": "SHIP-100-10-1731172800",
                "barcode_type": "CODE128",
                "entity_type": "shipment_item",
                "entity_id": 100,
                "shipment_item_id": 100,
                "label_format": "PDF",
                "label_size": "4x6",
                "label_data": "{\"product_name\": \"Steel Plate\", \"qty\": 50}"
            }
        }
    )


class BarcodeLabelGenerateDTO(BaseModel):
    """DTO for requesting barcode label generation (async)"""
    shipment_item_ids: List[int] = Field(description="List of shipment item IDs to generate labels for")
    barcode_type: BarcodeType = Field(default=BarcodeType.CODE128, description="Type of barcode to generate")
    label_format: str = Field(default="PDF", max_length=50, description="Label format")
    label_size: str = Field(default="4x6", max_length=20, description="Label size")
    include_material_info: bool = Field(default=True, description="Include material details on label")
    include_batch_info: bool = Field(default=True, description="Include batch/serial info on label")

    @field_validator('shipment_item_ids')
    @classmethod
    def validate_shipment_item_ids(cls, v: List[int]) -> List[int]:
        """Validate shipment item IDs list is not empty"""
        if not v:
            raise ValueError('shipment_item_ids cannot be empty')
        if any(item_id <= 0 for item_id in v):
            raise ValueError('All shipment_item_ids must be positive')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "shipment_item_ids": [100, 101, 102],
                "barcode_type": "QR_CODE",
                "label_format": "PDF",
                "label_size": "4x6",
                "include_material_info": True,
                "include_batch_info": True
            }
        }
    )


class BarcodeLabelResponse(BaseModel):
    """DTO for barcode label response"""
    id: int
    organization_id: int
    plant_id: int
    label_code: str
    barcode_value: str
    barcode_type: str
    entity_type: str
    entity_id: int
    shipment_item_id: Optional[int] = None
    label_format: str
    label_size: str
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    label_data: Optional[str] = None
    print_count: int
    last_printed_at: Optional[datetime] = None
    printed_by_user_id: Optional[int] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    presigned_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BarcodeGenerateRequestDTO(BaseModel):
    """DTO for async barcode generation request"""
    entity_type: str = Field(max_length=50, description="Entity type to generate barcode for")
    entity_id: int = Field(gt=0, description="Entity ID")
    barcode_type: BarcodeType = Field(default=BarcodeType.CODE128, description="Barcode type")
    prefix: str = Field(default="SHIP", max_length=10, description="Barcode prefix")
    auto_generate_label: bool = Field(default=True, description="Automatically generate label file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entity_type": "shipment_item",
                "entity_id": 100,
                "barcode_type": "QR_CODE",
                "prefix": "SHIP",
                "auto_generate_label": True
            }
        }
    )


# ==================== QR Code Scan DTOs ====================

class QRCodeScanCreateDTO(BaseModel):
    """DTO for creating a QR code scan event"""
    scan_code: str = Field(max_length=100, description="Scanned barcode/QR code value")
    barcode_type: Optional[BarcodeType] = Field(default=None, description="Type of barcode scanned")
    scan_location: Optional[str] = Field(default=None, max_length=200, description="Scan location/GPS")
    device_id: Optional[str] = Field(default=None, max_length=100, description="Scanner device ID")
    operation_context: Optional[str] = Field(default=None, max_length=100, description="Operation context (receiving, shipping, etc.)")
    work_order_id: Optional[int] = Field(default=None, gt=0, description="Associated work order ID")
    shipment_id: Optional[int] = Field(default=None, gt=0, description="Associated shipment ID")
    scan_data: Optional[str] = Field(default=None, description="Additional scan metadata (JSON)")

    @field_validator('scan_code')
    @classmethod
    def validate_scan_code(cls, v: str) -> str:
        """Validate scan code is not empty"""
        if not v or not v.strip():
            raise ValueError('scan_code cannot be empty')
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scan_code": "SHIP-100-10-1731172800",
                "barcode_type": "CODE128",
                "scan_location": "Receiving Dock A",
                "device_id": "SCANNER-001",
                "operation_context": "receiving",
                "shipment_id": 100,
                "scan_data": "{\"temperature\": 22.5, \"humidity\": 45}"
            }
        }
    )


class QRCodeScanResponse(BaseModel):
    """DTO for QR code scan response"""
    id: int
    organization_id: int
    plant_id: int
    scan_code: str
    barcode_type: Optional[str] = None
    scan_timestamp: datetime
    scan_location: Optional[str] = None
    device_id: Optional[str] = None
    scan_resolution: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    operation_context: Optional[str] = None
    work_order_id: Optional[int] = None
    shipment_id: Optional[int] = None
    scan_data: Optional[str] = None
    error_message: Optional[str] = None
    scanned_by_user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanLookupResponse(BaseModel):
    """DTO for scan lookup/resolution response with entity details"""
    scan_code: str
    scan_resolution: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_data: Optional[dict[str, Any]] = None
    scan_history: List[QRCodeScanResponse] = []
    last_scanned_at: Optional[datetime] = None
    total_scan_count: int = 0
    is_valid: bool = False
    validation_message: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scan_code": "SHIP-100-10-1731172800",
                "scan_resolution": "SUCCESS",
                "entity_type": "shipment_item",
                "entity_id": 100,
                "entity_data": {
                    "shipment_number": "SHIP-2025-001",
                    "material_description": "Steel Plate - 1/4 inch",
                    "quantity": 50.0,
                    "batch_number": "BATCH-2025-001"
                },
                "scan_history": [],
                "last_scanned_at": "2025-11-09T14:30:00Z",
                "total_scan_count": 5,
                "is_valid": True,
                "validation_message": "Shipment item found and active"
            }
        }
    )


# ==================== List/Pagination Response DTOs ====================

class ShipmentListResponse(BaseModel):
    """DTO for paginated shipment list response"""
    items: List[ShipmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BarcodeLabelListResponse(BaseModel):
    """DTO for paginated barcode label list response"""
    items: List[BarcodeLabelResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class QRCodeScanListResponse(BaseModel):
    """DTO for paginated QR scan list response"""
    items: List[QRCodeScanResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Error Response DTOs ====================

class ErrorResponse(BaseModel):
    """Generic error response"""
    detail: str


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    detail: list[dict]


class NotFoundErrorResponse(BaseModel):
    """Not found error response"""
    detail: str = "Resource not found"


class ConflictErrorResponse(BaseModel):
    """Conflict error response"""
    detail: str = "Conflict with current state"


# Update forward references for nested models
ShipmentResponse.model_rebuild()
