"""
Logistics Module API Router - Presentation layer endpoints for Logistics management.

Provides RESTful API for Shipment tracking, Barcode/QR generation, and Scanning operations with:
- JWT authentication (all endpoints)
- RLS context from authenticated user
- Pagination and filtering
- Shipment lifecycle management (DRAFT -> PLANNED -> IN_TRANSIT -> DELIVERED)
- Barcode/QR generation with async processing via PGMQ
- Scan tracking and analytics
- Request/response validation via Pydantic DTOs

Phase: Logistics & Shipment Tracking - Barcode/QR Integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import uuid

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.dtos.logistics_dto import (
    ShipmentCreateDTO,
    ShipmentUpdateDTO,
    ShipmentStatusUpdateDTO,
    ShipmentResponse,
    ShipmentListResponse,
    ShipmentItemCreateDTO,
    ShipmentItemResponse,
    BarcodeLabelCreateDTO,
    BarcodeLabelGenerateDTO,
    BarcodeLabelResponse,
    BarcodeLabelListResponse,
    BarcodeGenerateRequestDTO,
    QRCodeScanCreateDTO,
    QRCodeScanResponse,
    QRCodeScanListResponse,
    ScanLookupResponse,
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    ConflictErrorResponse,
)
from app.models.logistics import (
    Shipment,
    ShipmentItem,
    BarcodeLabel,
    QRCodeScan,
    ShipmentType,
    ShipmentStatus,
    BarcodeType,
    ScanResolution,
)
from app.infrastructure.repositories.logistics_repository import (
    ShipmentRepository,
    ShipmentItemRepository,
    BarcodeLabelRepository,
    QRCodeScanRepository,
)
from app.application.services.logistics_service import LogisticsService
from app.application.services.barcode_generation_service import BarcodeGenerationService
from app.infrastructure.storage.minio_client import MinIOClient
from app.infrastructure.messaging.pgmq_tasks import get_pgmq_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logistics", tags=["Logistics"])


# ==================== Dependency Injection ====================


def get_shipment_repository(db: Session = Depends(get_db)) -> ShipmentRepository:
    """Dependency injection for ShipmentRepository"""
    return ShipmentRepository(db)


def get_shipment_item_repository(db: Session = Depends(get_db)) -> ShipmentItemRepository:
    """Dependency injection for ShipmentItemRepository"""
    return ShipmentItemRepository(db)


def get_barcode_label_repository(db: Session = Depends(get_db)) -> BarcodeLabelRepository:
    """Dependency injection for BarcodeLabelRepository"""
    return BarcodeLabelRepository(db)


def get_scan_repository(db: Session = Depends(get_db)) -> QRCodeScanRepository:
    """Dependency injection for QRCodeScanRepository"""
    return QRCodeScanRepository(db)


def get_logistics_service(
    db: Session = Depends(get_db),
) -> LogisticsService:
    """Dependency injection for LogisticsService"""
    shipment_repo = ShipmentRepository(db)
    item_repo = ShipmentItemRepository(db)
    label_repo = BarcodeLabelRepository(db)
    scan_repo = QRCodeScanRepository(db)

    # Initialize barcode service with MinIO client
    try:
        minio_client = MinIOClient()
        barcode_service = BarcodeGenerationService(minio_client=minio_client)
    except Exception as e:
        logger.warning(f"Failed to initialize MinIO client: {e}. Barcode service will be limited.")
        barcode_service = None

    return LogisticsService(
        shipment_repo=shipment_repo,
        shipment_item_repo=item_repo,
        barcode_label_repo=label_repo,
        scan_repo=scan_repo,
        barcode_generation_service=barcode_service,
    )


def generate_shipment_number(org_id: int, plant_id: int, shipment_type: str) -> str:
    """
    Generate unique shipment number.

    Format: {TYPE_PREFIX}-{ORG_ID}-{PLANT_ID}-{UUID}
    Example: OUT-1-10-A3B2C1D4

    Args:
        org_id: Organization ID
        plant_id: Plant ID
        shipment_type: Shipment type (INBOUND, OUTBOUND, TRANSFER, RETURN)

    Returns:
        Generated shipment number
    """
    type_prefix_map = {
        "INBOUND": "IN",
        "OUTBOUND": "OUT",
        "TRANSFER": "TRF",
        "RETURN": "RET",
    }
    prefix = type_prefix_map.get(shipment_type, "SHP")
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{org_id}-{plant_id}-{unique_id}"


# ==================== Shipment Management Endpoints ====================


@router.post(
    "/shipments",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create shipment",
    description="Create a new shipment with optional items. Automatically generates shipment number.",
    responses={
        201: {"description": "Shipment created successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ConflictErrorResponse, "description": "Shipment number conflict"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def create_shipment(
    shipment_data: ShipmentCreateDTO,
    repository: ShipmentRepository = Depends(get_shipment_repository),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new shipment.

    **Required fields:**
    - shipment_type: Type of shipment (INBOUND, OUTBOUND, TRANSFER, RETURN)

    **Optional fields:**
    - carrier_name: Shipping carrier
    - tracking_number: Carrier tracking number
    - origin_location: Origin address
    - destination_location: Destination address
    - planned_ship_date: Planned shipment date
    - planned_delivery_date: Planned delivery date
    - freight_cost: Shipping cost
    - reference_document_type: Related document type (PO, WO, SO)
    - reference_document_id: Related document ID
    - notes: Additional notes

    **Example:**
    ```json
    {
        "shipment_type": "OUTBOUND",
        "carrier_name": "FedEx",
        "tracking_number": "1234567890",
        "origin_location": "Plant A, Chicago, IL",
        "destination_location": "Warehouse B, Dallas, TX",
        "planned_ship_date": "2025-11-10T08:00:00Z",
        "planned_delivery_date": "2025-11-12T17:00:00Z",
        "freight_cost": 250.00,
        "reference_document_type": "SO",
        "reference_document_id": 5001
    }
    ```
    """
    try:
        org_id = current_user.organization_id
        plant_id = current_user.plant_id
        user_id = current_user.id

        logger.info(f"Creating shipment type {shipment_data.shipment_type} (user: {user_id})")

        # Generate shipment number
        shipment_number = generate_shipment_number(org_id, plant_id, shipment_data.shipment_type.value)

        # Prepare shipment data
        shipment_dict = {
            "organization_id": org_id,
            "plant_id": plant_id,
            "shipment_number": shipment_number,
            "shipment_type": shipment_data.shipment_type.value,
            "shipment_status": ShipmentStatus.DRAFT.value,
            "carrier_name": shipment_data.carrier_name,
            "tracking_number": shipment_data.tracking_number,
            "origin_location": shipment_data.origin_location,
            "destination_location": shipment_data.destination_location,
            "planned_ship_date": shipment_data.planned_ship_date,
            "planned_delivery_date": shipment_data.planned_delivery_date,
            "weight_uom": shipment_data.weight_uom,
            "volume_uom": shipment_data.volume_uom,
            "freight_cost": shipment_data.freight_cost,
            "currency_code": shipment_data.currency_code,
            "reference_document_type": shipment_data.reference_document_type,
            "reference_document_id": shipment_data.reference_document_id,
            "notes": shipment_data.notes,
            "created_by_user_id": user_id,
        }

        # Create shipment via repository
        db_shipment = repository.create(shipment_dict)

        logger.info(f"Shipment created successfully: {shipment_number}")

        # Map to response DTO
        return ShipmentResponse.model_validate(db_shipment)

    except ValueError as e:
        logger.error(f"Validation error creating shipment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create shipment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shipment"
        )


@router.get(
    "/shipments",
    response_model=ShipmentListResponse,
    summary="List shipments",
    description="List shipments with optional filtering by status, type, and date range. Supports pagination.",
    responses={
        200: {"description": "Shipments retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def list_shipments(
    status_filter: Optional[ShipmentStatus] = Query(None, alias="status", description="Filter by shipment status"),
    type_filter: Optional[ShipmentType] = Query(None, alias="type", description="Filter by shipment type"),
    date_from: Optional[datetime] = Query(None, description="Filter by planned ship date (start)"),
    date_to: Optional[datetime] = Query(None, description="Filter by planned ship date (end)"),
    tracking_number: Optional[str] = Query(None, description="Filter by tracking number"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    repository: ShipmentRepository = Depends(get_shipment_repository),
    current_user: dict = Depends(get_current_user),
):
    """
    List shipments with filtering and pagination.

    **Query Parameters:**
    - status: Filter by status (DRAFT, PLANNED, IN_TRANSIT, DELIVERED, CANCELLED, DELAYED)
    - type: Filter by type (INBOUND, OUTBOUND, TRANSFER, RETURN)
    - date_from: Filter shipments with planned_ship_date >= this date
    - date_to: Filter shipments with planned_ship_date <= this date
    - tracking_number: Filter by tracking number (partial match)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)

    **Returns:**
    Paginated list of shipments with total count and page information.

    **Example:**
    ```
    GET /logistics/shipments?status=IN_TRANSIT&page=1&page_size=20
    ```
    """
    try:
        org_id = current_user.organization_id
        plant_id = current_user.plant_id

        logger.info(f"Listing shipments for org {org_id}, plant {plant_id} (page {page})")

        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter.value
        if type_filter:
            filters["type"] = type_filter.value
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if tracking_number:
            filters["tracking_number"] = tracking_number

        # Get paginated results
        result = repository.list_by_organization(
            org_id=org_id,
            plant_id=plant_id,
            filters=filters,
            page=page,
            page_size=page_size,
        )

        # Map to response DTOs
        items = [ShipmentResponse.model_validate(s) for s in result["items"]]

        return ShipmentListResponse(
            items=items,
            total=result["total"],
            page=page,
            page_size=page_size,
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list shipments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list shipments"
        )


@router.get(
    "/shipments/{shipment_id}",
    response_model=ShipmentResponse,
    summary="Get shipment details",
    description="Retrieve a shipment by ID with all items. RLS filtering is automatic.",
    responses={
        200: {"description": "Shipment found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shipment not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_shipment(
    shipment_id: int,
    repository: ShipmentRepository = Depends(get_shipment_repository),
    current_user: dict = Depends(get_current_user),
):
    """
    Get shipment by ID with all items.

    **Path Parameters:**
    - shipment_id: Shipment ID

    **Returns:**
    Complete shipment details including all shipment items.

    RLS filtering is automatically applied from the authenticated user's organization/plant context.
    """
    try:
        logger.info(f"Fetching shipment ID: {shipment_id}")

        shipment = repository.get_by_id(shipment_id)

        if not shipment:
            logger.warning(f"Shipment {shipment_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment {shipment_id} not found"
            )

        return ShipmentResponse.model_validate(shipment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get shipment {shipment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shipment"
        )


@router.put(
    "/shipments/{shipment_id}",
    response_model=ShipmentResponse,
    summary="Update shipment",
    description="Update shipment details. Only specified fields will be updated.",
    responses={
        200: {"description": "Shipment updated successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shipment not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def update_shipment(
    shipment_id: int,
    shipment_data: ShipmentUpdateDTO,
    repository: ShipmentRepository = Depends(get_shipment_repository),
    current_user: dict = Depends(get_current_user),
):
    """
    Update shipment details (partial update).

    **Path Parameters:**
    - shipment_id: Shipment ID

    **Optional fields to update:**
    - carrier_name
    - tracking_number
    - origin_location
    - destination_location
    - planned_ship_date
    - actual_ship_date
    - planned_delivery_date
    - actual_delivery_date
    - total_weight
    - total_volume
    - freight_cost
    - notes

    **Example:**
    ```json
    {
        "actual_ship_date": "2025-11-10T09:30:00Z",
        "tracking_number": "1234567890",
        "notes": "Shipped on time"
    }
    ```
    """
    try:
        logger.info(f"Updating shipment {shipment_id}")

        # Check if shipment exists
        shipment = repository.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment {shipment_id} not found"
            )

        # Build update dict with only provided fields
        update_dict = shipment_data.model_dump(exclude_unset=True)

        if not update_dict:
            logger.warning(f"No fields provided for update on shipment {shipment_id}")
            return ShipmentResponse.model_validate(shipment)

        # Update shipment
        updated_shipment = repository.update(shipment_id, update_dict)

        logger.info(f"Shipment {shipment_id} updated successfully")
        return ShipmentResponse.model_validate(updated_shipment)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating shipment {shipment_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update shipment {shipment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update shipment"
        )


@router.delete(
    "/shipments/{shipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete shipment",
    description="Delete a shipment. Only DRAFT shipments can be deleted.",
    responses={
        204: {"description": "Shipment deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shipment not found"},
        409: {"model": ConflictErrorResponse, "description": "Cannot delete shipment (not in DRAFT status)"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def delete_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    repository: ShipmentRepository = Depends(get_shipment_repository),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a shipment.

    **Path Parameters:**
    - shipment_id: Shipment ID

    **Business Rules:**
    - Only shipments in DRAFT status can be deleted
    - All shipment items will be cascade deleted
    """
    try:
        logger.info(f"Deleting shipment {shipment_id}")

        # Check if shipment exists
        shipment = repository.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment {shipment_id} not found"
            )

        # Check if shipment is in DRAFT status
        if shipment.shipment_status != ShipmentStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete shipment with status {shipment.shipment_status.value}. Only DRAFT shipments can be deleted."
            )

        # Delete shipment (cascade deletes items via database constraint)
        db.delete(shipment)
        db.commit()

        logger.info(f"Shipment {shipment_id} deleted successfully")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete shipment {shipment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete shipment"
        )


@router.post(
    "/shipments/{shipment_id}/items",
    response_model=List[ShipmentItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add items to shipment",
    description="Add one or more items to an existing shipment.",
    responses={
        201: {"description": "Items added successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shipment not found"},
        409: {"model": ConflictErrorResponse, "description": "Cannot add items (shipment status)"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def add_shipment_items(
    shipment_id: int,
    items: List[ShipmentItemCreateDTO],
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Add items to an existing shipment.

    **Path Parameters:**
    - shipment_id: Shipment ID

    **Request Body:**
    List of shipment items to add.

    **Business Rules:**
    - Can only add items to shipments in DRAFT status
    - Line numbers will be auto-assigned if not provided

    **Example:**
    ```json
    [
        {
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
    ]
    ```
    """
    try:
        logger.info(f"Adding {len(items)} items to shipment {shipment_id}")

        # Convert DTOs to dicts
        items_data = [item.model_dump() for item in items]

        # Add items via service
        created_items = service.add_shipment_items(shipment_id, items_data)

        logger.info(f"Added {len(created_items)} items to shipment {shipment_id}")

        # Map to response DTOs
        return [ShipmentItemResponse(**item) for item in created_items]

    except ValueError as e:
        logger.error(f"Validation error adding items to shipment {shipment_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "cannot add items" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add items to shipment {shipment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add items to shipment"
        )


@router.post(
    "/shipments/{shipment_id}/pack",
    response_model=ShipmentResponse,
    summary="Pack shipment",
    description="Mark shipment as packed (status transition: DRAFT -> PLANNED).",
    responses={
        200: {"description": "Shipment packed successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shipment not found"},
        409: {"model": ConflictErrorResponse, "description": "Invalid status transition"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def pack_shipment(
    shipment_id: int,
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Pack shipment and transition to PLANNED status.

    **Path Parameters:**
    - shipment_id: Shipment ID

    **Status Transition:**
    - DRAFT -> PLANNED

    **Business Rules:**
    - Shipment must be in DRAFT status
    - Shipment must have at least one item
    """
    try:
        user_id = current_user.id
        logger.info(f"Packing shipment {shipment_id} (user: {user_id})")

        # Pack shipment via service
        packed_shipment = service.pack_shipment(shipment_id, user_id)

        logger.info(f"Shipment {shipment_id} packed successfully")
        return ShipmentResponse(**packed_shipment)

    except ValueError as e:
        logger.error(f"Error packing shipment {shipment_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to pack shipment {shipment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pack shipment"
        )


@router.post(
    "/shipments/{shipment_id}/ship",
    response_model=ShipmentResponse,
    summary="Ship shipment",
    description="Ship shipment with tracking number (status transition: PLANNED -> IN_TRANSIT).",
    responses={
        200: {"description": "Shipment shipped successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shipment not found"},
        409: {"model": ConflictErrorResponse, "description": "Invalid status transition"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def ship_shipment(
    shipment_id: int,
    tracking_number: Optional[str] = Query(None, description="Carrier tracking number"),
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Ship shipment and transition to IN_TRANSIT status.

    **Path Parameters:**
    - shipment_id: Shipment ID

    **Query Parameters:**
    - tracking_number: Optional carrier tracking number

    **Status Transition:**
    - PLANNED -> IN_TRANSIT

    **Business Rules:**
    - Shipment must be in PLANNED status
    - Records actual_ship_date as current timestamp
    """
    try:
        user_id = current_user.id
        logger.info(f"Shipping shipment {shipment_id} (user: {user_id}, tracking: {tracking_number})")

        # Ship shipment via service
        shipped_shipment = service.ship_shipment(shipment_id, user_id, tracking_number)

        logger.info(f"Shipment {shipment_id} shipped successfully")
        return ShipmentResponse(**shipped_shipment)

    except ValueError as e:
        logger.error(f"Error shipping shipment {shipment_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to ship shipment {shipment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ship shipment"
        )


@router.post(
    "/shipments/{shipment_id}/deliver",
    response_model=ShipmentResponse,
    summary="Mark shipment as delivered",
    description="Mark shipment as delivered (status transition: IN_TRANSIT -> DELIVERED).",
    responses={
        200: {"description": "Shipment delivered successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shipment not found"},
        409: {"model": ConflictErrorResponse, "description": "Invalid status transition"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def deliver_shipment(
    shipment_id: int,
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Mark shipment as delivered and transition to DELIVERED status.

    **Path Parameters:**
    - shipment_id: Shipment ID

    **Status Transition:**
    - IN_TRANSIT -> DELIVERED

    **Business Rules:**
    - Shipment must be in IN_TRANSIT status
    - Records actual_delivery_date as current timestamp
    """
    try:
        logger.info(f"Marking shipment {shipment_id} as delivered")

        # Deliver shipment via service
        delivered_shipment = service.deliver_shipment(shipment_id)

        logger.info(f"Shipment {shipment_id} delivered successfully")
        return ShipmentResponse(**delivered_shipment)

    except ValueError as e:
        logger.error(f"Error delivering shipment {shipment_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to deliver shipment {shipment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deliver shipment"
        )


@router.post(
    "/shipments/{shipment_id}/cancel",
    response_model=ShipmentResponse,
    summary="Cancel shipment",
    description="Cancel shipment (status transition: any -> CANCELLED).",
    responses={
        200: {"description": "Shipment cancelled successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shipment not found"},
        409: {"model": ConflictErrorResponse, "description": "Cannot cancel delivered shipment"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def cancel_shipment(
    shipment_id: int,
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Cancel shipment and transition to CANCELLED status.

    **Path Parameters:**
    - shipment_id: Shipment ID

    **Status Transition:**
    - Any status (except DELIVERED) -> CANCELLED

    **Business Rules:**
    - Cannot cancel shipments that are already DELIVERED
    """
    try:
        logger.info(f"Cancelling shipment {shipment_id}")

        # Cancel shipment via service
        cancelled_shipment = service.cancel_shipment(shipment_id)

        logger.info(f"Shipment {shipment_id} cancelled successfully")
        return ShipmentResponse(**cancelled_shipment)

    except ValueError as e:
        logger.error(f"Error cancelling shipment {shipment_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel shipment {shipment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel shipment"
        )


@router.get(
    "/shipments/overdue",
    response_model=List[ShipmentResponse],
    summary="Get overdue shipments",
    description="Get shipments that are overdue (planned_ship_date in past, not yet shipped).",
    responses={
        200: {"description": "Overdue shipments retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_overdue_shipments(
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get overdue shipments.

    **Returns:**
    List of shipments where planned_ship_date is in the past and shipment is not yet shipped
    (status is DRAFT or PLANNED).

    **Business Logic:**
    - planned_ship_date < current date
    - status in (DRAFT, PLANNED)
    """
    try:
        org_id = current_user.organization_id
        plant_id = current_user.plant_id

        logger.info(f"Fetching overdue shipments for org {org_id}, plant {plant_id}")

        # Get overdue shipments via service
        overdue_shipments = service.get_overdue_shipments(org_id, plant_id)

        # Map to response DTOs
        return [ShipmentResponse(**s) for s in overdue_shipments]

    except Exception as e:
        logger.error(f"Failed to get overdue shipments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get overdue shipments"
        )


# ==================== Barcode/QR Management Endpoints ====================


@router.post(
    "/barcodes/generate",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate barcode/QR code",
    description="Queue barcode/QR code generation job (async via PGMQ).",
    responses={
        202: {"description": "Barcode generation job queued"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def generate_barcode(
    request: BarcodeGenerateRequestDTO,
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Queue barcode/QR code generation job.

    **Request Body:**
    - entity_type: Entity type (shipment_item, material, work_order, etc.)
    - entity_id: Entity ID
    - barcode_type: Barcode type (CODE128, QR_CODE, DATA_MATRIX, etc.)
    - prefix: Barcode prefix (default: "SHIP")
    - auto_generate_label: Auto-generate label file (default: true)

    **Returns:**
    Job information with label_id and job_id for tracking.

    **Processing:**
    - Job is queued in PGMQ for async processing
    - Background worker will generate barcode and store in MinIO
    - Check `/barcodes/{label_id}` to get the generated label

    **Example:**
    ```json
    {
        "entity_type": "shipment_item",
        "entity_id": 100,
        "barcode_type": "QR_CODE",
        "prefix": "SHIP",
        "auto_generate_label": true
    }
    ```
    """
    try:
        org_id = current_user.organization_id
        plant_id = current_user.plant_id
        user_id = current_user.id

        logger.info(f"Queueing barcode generation for {request.entity_type}/{request.entity_id}")

        # Generate barcode value
        barcode_value = f"{request.prefix}-{request.entity_id}-{int(datetime.now().timestamp())}"

        # Queue generation job via service
        result = service.generate_barcode_async(
            org_id=org_id,
            plant_id=plant_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            barcode_type=request.barcode_type.value,
            barcode_value=barcode_value,
            created_by_user_id=user_id,
        )

        logger.info(f"Barcode generation job queued: {result['job_id']}")

        return {
            "label_id": result["label_id"],
            "job_id": result["job_id"],
            "status": "queued",
            "barcode_value": barcode_value,
            "message": f"Barcode generation job queued. Check /barcodes/{result['label_id']} for result."
        }

    except ValueError as e:
        logger.error(f"Validation error queueing barcode generation: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to queue barcode generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue barcode generation"
        )


@router.post(
    "/barcodes/generate-batch",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch generate barcodes",
    description="Generate barcodes for multiple shipment items in batch.",
    responses={
        202: {"description": "Batch barcode generation jobs queued"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def generate_barcodes_batch(
    request: BarcodeLabelGenerateDTO,
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate barcodes for multiple shipment items in batch.

    **Request Body:**
    - shipment_item_ids: List of shipment item IDs
    - barcode_type: Barcode type (default: CODE128)
    - label_format: Label format (PDF, PNG, ZPL)
    - label_size: Label size (4x6, 2x3, etc.)
    - include_material_info: Include material details on label
    - include_batch_info: Include batch/serial info on label

    **Returns:**
    Batch job information with list of queued jobs.

    **Example:**
    ```json
    {
        "shipment_item_ids": [100, 101, 102],
        "barcode_type": "QR_CODE",
        "label_format": "PDF",
        "label_size": "4x6"
    }
    ```
    """
    try:
        org_id = current_user.organization_id
        plant_id = current_user.plant_id
        user_id = current_user.id

        logger.info(f"Batch generating barcodes for {len(request.shipment_item_ids)} items")

        queued_jobs = []

        for item_id in request.shipment_item_ids:
            # Generate barcode value
            barcode_value = f"SHIP-{item_id}-{int(datetime.now().timestamp())}"

            # Queue generation job
            result = service.generate_barcode_async(
                org_id=org_id,
                plant_id=plant_id,
                entity_type="shipment_item",
                entity_id=item_id,
                barcode_type=request.barcode_type.value,
                barcode_value=barcode_value,
                created_by_user_id=user_id,
                label_format=request.label_format,
            )

            queued_jobs.append({
                "item_id": item_id,
                "label_id": result["label_id"],
                "job_id": result["job_id"],
                "barcode_value": barcode_value,
            })

        logger.info(f"Queued {len(queued_jobs)} barcode generation jobs")

        return {
            "total_items": len(request.shipment_item_ids),
            "jobs_queued": len(queued_jobs),
            "jobs": queued_jobs,
            "message": f"Queued {len(queued_jobs)} barcode generation jobs"
        }

    except ValueError as e:
        logger.error(f"Validation error in batch barcode generation: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to queue batch barcode generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue batch barcode generation"
        )


@router.get(
    "/barcodes/{label_id}",
    response_model=BarcodeLabelResponse,
    summary="Get barcode label",
    description="Get barcode label details including file URL.",
    responses={
        200: {"description": "Label found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Label not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_barcode_label(
    label_id: int,
    repository: BarcodeLabelRepository = Depends(get_barcode_label_repository),
    current_user: dict = Depends(get_current_user),
):
    """
    Get barcode label by ID.

    **Path Parameters:**
    - label_id: Label ID

    **Returns:**
    Label details including file_path, file_url, and presigned download URL (if available).
    """
    try:
        logger.info(f"Fetching barcode label {label_id}")

        label = repository.get_by_id(label_id)

        if not label:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Barcode label {label_id} not found"
            )

        return BarcodeLabelResponse.model_validate(label)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get barcode label {label_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve barcode label"
        )


@router.post(
    "/barcodes/{label_id}/print",
    response_model=BarcodeLabelResponse,
    summary="Mark barcode as printed",
    description="Record that a barcode label was printed.",
    responses={
        200: {"description": "Label marked as printed"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Label not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def mark_barcode_printed(
    label_id: int,
    repository: BarcodeLabelRepository = Depends(get_barcode_label_repository),
    current_user: dict = Depends(get_current_user),
):
    """
    Mark barcode label as printed.

    **Path Parameters:**
    - label_id: Label ID

    **Updates:**
    - Increments print_count
    - Sets last_printed_at to current timestamp
    - Records printed_by_user_id
    """
    try:
        user_id = current_user.id
        logger.info(f"Marking barcode label {label_id} as printed (user: {user_id})")

        # Mark as printed
        label = repository.mark_printed(label_id, user_id)

        if not label:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Barcode label {label_id} not found"
            )

        logger.info(f"Label {label_id} marked as printed")
        return BarcodeLabelResponse.model_validate(label)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark label {label_id} as printed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark label as printed"
        )


@router.get(
    "/barcodes/entity/{entity_type}/{entity_id}",
    response_model=List[BarcodeLabelResponse],
    summary="Get labels for entity",
    description="Get all barcode labels for a specific entity.",
    responses={
        200: {"description": "Labels retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_labels_for_entity(
    entity_type: str,
    entity_id: int,
    repository: BarcodeLabelRepository = Depends(get_barcode_label_repository),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all barcode labels for a specific entity.

    **Path Parameters:**
    - entity_type: Entity type (shipment_item, material, work_order, etc.)
    - entity_id: Entity ID

    **Returns:**
    List of all barcode labels associated with the entity.
    """
    try:
        org_id = current_user.organization_id

        logger.info(f"Fetching labels for {entity_type}/{entity_id}")

        labels = repository.get_by_entity(entity_type, entity_id)

        return [BarcodeLabelResponse.model_validate(label) for label in labels]

    except Exception as e:
        logger.error(f"Failed to get labels for {entity_type}/{entity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve labels"
        )


# ==================== Scanning Operations Endpoints ====================


@router.post(
    "/scan",
    response_model=QRCodeScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record scan event",
    description="Record a barcode/QR code scan event with entity resolution.",
    responses={
        201: {"description": "Scan recorded successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def record_scan(
    scan_data: QRCodeScanCreateDTO,
    repository: QRCodeScanRepository = Depends(get_scan_repository),
    label_repo: BarcodeLabelRepository = Depends(get_barcode_label_repository),
    current_user: dict = Depends(get_current_user),
):
    """
    Record a barcode/QR code scan event.

    **Request Body:**
    - scan_code: Scanned barcode/QR code value
    - barcode_type: Type of barcode scanned (optional)
    - scan_location: Scan location (optional)
    - device_id: Scanner device ID (optional)
    - operation_context: Operation context (receiving, shipping, etc.)
    - work_order_id: Associated work order (optional)
    - shipment_id: Associated shipment (optional)
    - scan_data: Additional metadata (JSON string)

    **Processing:**
    - Resolves scan code to entity (if exists in system)
    - Records scan event with timestamp and user
    - Sets scan_resolution based on lookup result

    **Example:**
    ```json
    {
        "scan_code": "SHIP-100-10-1731172800",
        "barcode_type": "CODE128",
        "scan_location": "Receiving Dock A",
        "device_id": "SCANNER-001",
        "operation_context": "receiving",
        "shipment_id": 100
    }
    ```
    """
    try:
        org_id = current_user.organization_id
        plant_id = current_user.plant_id
        user_id = current_user.id

        logger.info(f"Recording scan: {scan_data.scan_code} (user: {user_id})")

        # Lookup barcode to resolve entity
        label = label_repo.get_by_value(scan_data.scan_code)

        if label:
            scan_resolution = ScanResolution.SUCCESS
            entity_type = label.entity_type
            entity_id = label.entity_id
        else:
            scan_resolution = ScanResolution.NOT_FOUND
            entity_type = None
            entity_id = None

        # Create scan record
        scan_dict = {
            "organization_id": org_id,
            "plant_id": plant_id,
            "scan_code": scan_data.scan_code,
            "barcode_type": scan_data.barcode_type.value if scan_data.barcode_type else None,
            "scan_timestamp": datetime.now(),
            "scan_location": scan_data.scan_location,
            "device_id": scan_data.device_id,
            "scan_resolution": scan_resolution.value,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "operation_context": scan_data.operation_context,
            "work_order_id": scan_data.work_order_id,
            "shipment_id": scan_data.shipment_id,
            "scan_data": scan_data.scan_data,
            "scanned_by_user_id": user_id,
        }

        db_scan = repository.create(scan_dict)

        logger.info(f"Scan recorded: {db_scan.id} (resolution: {scan_resolution.value})")

        return QRCodeScanResponse.model_validate(db_scan)

    except ValueError as e:
        logger.error(f"Validation error recording scan: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to record scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record scan"
        )


@router.post(
    "/scan/lookup",
    response_model=ScanLookupResponse,
    summary="Lookup entity by barcode/QR",
    description="Look up entity by barcode/QR code value without recording a scan.",
    responses={
        200: {"description": "Lookup completed"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def lookup_barcode(
    scan_code: str = Query(..., description="Barcode/QR code value to lookup"),
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Look up entity by barcode/QR code value.

    **Query Parameters:**
    - scan_code: Barcode/QR code value to lookup

    **Returns:**
    - scan_code: The scanned code
    - scan_resolution: Resolution status (SUCCESS, NOT_FOUND, etc.)
    - entity_type: Entity type (if found)
    - entity_id: Entity ID (if found)
    - entity_data: Entity details (if found)
    - scan_history: Recent scan history for this code
    - is_valid: Whether the code is valid and active

    **Example:**
    ```
    POST /logistics/scan/lookup?scan_code=SHIP-100-10-1731172800
    ```
    """
    try:
        logger.info(f"Looking up barcode: {scan_code}")

        # Lookup via service
        entity = service.lookup_barcode(scan_code)

        if entity:
            # Get scan history for this code
            scan_history_result = service.get_scan_history(
                org_id=current_user.organization_id,
                filters={"scan_code": scan_code},
                page=1,
                page_size=10,
            )

            return ScanLookupResponse(
                scan_code=scan_code,
                scan_resolution=ScanResolution.SUCCESS.value,
                entity_type=entity["entity_type"],
                entity_id=entity["entity_id"],
                entity_data=entity,
                scan_history=[QRCodeScanResponse(**s) for s in scan_history_result.get("items", [])],
                last_scanned_at=scan_history_result["items"][0]["scanned_at"] if scan_history_result.get("items") else None,
                total_scan_count=scan_history_result.get("total", 0),
                is_valid=True,
                validation_message="Entity found and active",
            )
        else:
            return ScanLookupResponse(
                scan_code=scan_code,
                scan_resolution=ScanResolution.NOT_FOUND.value,
                entity_type=None,
                entity_id=None,
                entity_data=None,
                scan_history=[],
                total_scan_count=0,
                is_valid=False,
                validation_message="Barcode not found in system",
            )

    except Exception as e:
        logger.error(f"Failed to lookup barcode {scan_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lookup barcode"
        )


@router.get(
    "/scan/history",
    response_model=QRCodeScanListResponse,
    summary="Get scan history",
    description="Get scan history with filtering and pagination.",
    responses={
        200: {"description": "Scan history retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_scan_history(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    scan_code: Optional[str] = Query(None, description="Filter by scan code"),
    start_date: Optional[datetime] = Query(None, description="Filter by scan date (start)"),
    end_date: Optional[datetime] = Query(None, description="Filter by scan date (end)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get scan history with filtering and pagination.

    **Query Parameters:**
    - user_id: Filter by user who performed the scan
    - entity_type: Filter by entity type
    - entity_id: Filter by entity ID
    - scan_code: Filter by specific scan code
    - start_date: Filter by scan date (start)
    - end_date: Filter by scan date (end)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)

    **Returns:**
    Paginated list of scan events.

    **Example:**
    ```
    GET /logistics/scan/history?entity_type=shipment_item&entity_id=100&page=1&page_size=20
    ```
    """
    try:
        org_id = current_user.organization_id

        logger.info(f"Fetching scan history for org {org_id} (page {page})")

        # Build filters
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if entity_type:
            filters["entity_type"] = entity_type
        if entity_id:
            filters["entity_id"] = entity_id
        if scan_code:
            filters["scan_code"] = scan_code
        if start_date:
            filters["start_time"] = start_date
        if end_date:
            filters["end_time"] = end_date

        # Get scan history via service
        result = service.get_scan_history(
            org_id=org_id,
            filters=filters,
            page=page,
            page_size=page_size,
        )

        # Map to response DTOs
        items = [QRCodeScanResponse(**s) for s in result.get("items", [])]

        return QRCodeScanListResponse(
            items=items,
            total=result.get("total", 0),
            page=page,
            page_size=page_size,
            total_pages=result.get("total_pages", 0),
        )

    except Exception as e:
        logger.error(f"Failed to get scan history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scan history"
        )


@router.get(
    "/scan/analytics",
    response_model=dict,
    summary="Get scan analytics",
    description="Get scan analytics and statistics for a time period.",
    responses={
        200: {"description": "Analytics retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_scan_analytics(
    start_date: datetime = Query(..., description="Start date for analytics"),
    end_date: datetime = Query(..., description="End date for analytics"),
    service: LogisticsService = Depends(get_logistics_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get scan analytics and statistics.

    **Query Parameters:**
    - start_date: Start date for analytics period
    - end_date: End date for analytics period

    **Returns:**
    - total_scans: Total number of scans
    - resolved_scans: Number of successfully resolved scans
    - not_found_scans: Number of scans that couldn't be resolved
    - success_rate: Percentage of successful scans
    - scans_by_type: Breakdown by entity type
    - scans_by_user: Top users by scan count
    - scans_by_day: Daily scan counts

    **Example:**
    ```
    GET /logistics/scan/analytics?start_date=2025-11-01T00:00:00Z&end_date=2025-11-10T23:59:59Z
    ```
    """
    try:
        org_id = current_user.organization_id

        logger.info(f"Fetching scan analytics for org {org_id} ({start_date} to {end_date})")

        # Get analytics via service
        analytics = service.get_scan_analytics(org_id, start_date, end_date)

        return analytics

    except Exception as e:
        logger.error(f"Failed to get scan analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scan analytics"
        )
