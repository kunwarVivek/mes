"""
API endpoints for Traceability module (Lot/Serial tracking, Genealogy)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.dtos.traceability_dto import (
    LotBatchCreateDTO,
    LotBatchUpdateDTO,
    LotBatchReserveDTO,
    LotBatchConsumeDTO,
    LotBatchResponse,
    SerialNumberCreateDTO,
    SerialNumberUpdateDTO,
    SerialNumberShipDTO,
    SerialNumberResponse,
    TraceabilityLinkCreateDTO,
    TraceabilityLinkResponse,
    GenealogyQueryRequest,
    GenealogyRecordResponse,
    WhereUsedRequest,
    WhereFromRequest,
    GenealogyTreeResponse,
    RecallReportRequest,
    RecallReportResponse,
)
from app.application.services.traceability_service import (
    LotBatchService,
    SerialNumberService,
    TraceabilityLinkService,
    GenealogyService,
    RecallReportService,
)

router = APIRouter(prefix="/traceability", tags=["traceability"])


# ==================== Lot Batch Endpoints ====================

@router.post("/lots", response_model=LotBatchResponse, status_code=status.HTTP_201_CREATED)
def create_lot(
    lot_data: LotBatchCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new lot batch"""
    service = LotBatchService(db)
    try:
        return service.create_lot(lot_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/lots", response_model=List[LotBatchResponse])
def list_lots(
    organization_id: int = Query(..., gt=0),
    material_id: Optional[int] = Query(None),
    quality_status: Optional[str] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List lot batches"""
    service = LotBatchService(db)
    return service.list_lots(organization_id, skip, limit, material_id, quality_status, active_only)


@router.get("/lots/{lot_id}", response_model=LotBatchResponse)
def get_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get lot batch by ID"""
    service = LotBatchService(db)
    lot = service.get_lot(lot_id)
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lot {lot_id} not found")
    return lot


@router.get("/lots/by-lot-number/{lot_number}", response_model=LotBatchResponse)
def get_lot_by_number(
    lot_number: str,
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get lot batch by lot number"""
    service = LotBatchService(db)
    lot = service.get_by_lot_number(organization_id, lot_number)
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lot '{lot_number}' not found")
    return lot


@router.get("/lots/by-material/{material_id}", response_model=List[LotBatchResponse])
def list_lots_by_material(
    material_id: int,
    quality_status: Optional[str] = Query(None),
    available_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List lot batches for a material"""
    service = LotBatchService(db)
    return service.list_by_material(material_id, quality_status, available_only)


@router.get("/lots/expiring-soon", response_model=List[LotBatchResponse])
def list_lots_expiring_soon(
    organization_id: int = Query(..., gt=0),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List lots expiring within specified days"""
    service = LotBatchService(db)
    return service.list_expiring_soon(organization_id, days)


@router.get("/lots/needing-retest", response_model=List[LotBatchResponse])
def list_lots_needing_retest(
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List lots needing retest"""
    service = LotBatchService(db)
    return service.list_needing_retest(organization_id)


@router.patch("/lots/{lot_id}", response_model=LotBatchResponse)
def update_lot(
    lot_id: int,
    lot_data: LotBatchUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update lot batch"""
    service = LotBatchService(db)
    user_id = current_user.get("id", 0)
    lot = service.update_lot(lot_id, lot_data, user_id)
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lot {lot_id} not found")
    return lot


@router.post("/lots/{lot_id}/reserve", response_model=LotBatchResponse)
def reserve_lot_quantity(
    lot_id: int,
    reserve_data: LotBatchReserveDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Reserve quantity from lot"""
    service = LotBatchService(db)
    try:
        return service.reserve_quantity(lot_id, reserve_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/lots/{lot_id}/consume", response_model=LotBatchResponse)
def consume_lot_quantity(
    lot_id: int,
    consume_data: LotBatchConsumeDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Consume quantity from lot"""
    service = LotBatchService(db)
    try:
        return service.consume_quantity(lot_id, consume_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/lots/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete lot batch (soft delete)"""
    service = LotBatchService(db)
    if not service.delete_lot(lot_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lot {lot_id} not found")


# ==================== Serial Number Endpoints ====================

@router.post("/serials", response_model=SerialNumberResponse, status_code=status.HTTP_201_CREATED)
def create_serial(
    serial_data: SerialNumberCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new serial number"""
    service = SerialNumberService(db)
    try:
        return service.create_serial(serial_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/serials", response_model=List[SerialNumberResponse])
def list_serials(
    organization_id: int = Query(..., gt=0),
    material_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List serial numbers"""
    service = SerialNumberService(db)
    return service.list_serials(organization_id, skip, limit, material_id, status, customer_id)


@router.get("/serials/{serial_id}", response_model=SerialNumberResponse)
def get_serial(
    serial_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get serial number by ID"""
    service = SerialNumberService(db)
    serial = service.get_serial(serial_id)
    if not serial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Serial {serial_id} not found")
    return serial


@router.get("/serials/by-serial-number/{serial_number}", response_model=SerialNumberResponse)
def get_serial_by_number(
    serial_number: str,
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get serial number by serial"""
    service = SerialNumberService(db)
    serial = service.get_by_serial_number(organization_id, serial_number)
    if not serial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Serial '{serial_number}' not found")
    return serial


@router.get("/serials/by-lot/{lot_batch_id}", response_model=List[SerialNumberResponse])
def list_serials_by_lot(
    lot_batch_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List serial numbers for a lot batch"""
    service = SerialNumberService(db)
    return service.list_by_lot(lot_batch_id)


@router.get("/serials/by-customer/{customer_id}", response_model=List[SerialNumberResponse])
def list_serials_by_customer(
    customer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List serial numbers for a customer"""
    service = SerialNumberService(db)
    return service.list_by_customer(customer_id, skip, limit)


@router.get("/serials/in-warranty", response_model=List[SerialNumberResponse])
def list_serials_in_warranty(
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List serial numbers currently under warranty"""
    service = SerialNumberService(db)
    return service.list_in_warranty(organization_id)


@router.patch("/serials/{serial_id}", response_model=SerialNumberResponse)
def update_serial(
    serial_id: int,
    serial_data: SerialNumberUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update serial number"""
    service = SerialNumberService(db)
    user_id = current_user.get("id", 0)
    serial = service.update_serial(serial_id, serial_data, user_id)
    if not serial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Serial {serial_id} not found")
    return serial


@router.post("/serials/{serial_id}/ship", response_model=SerialNumberResponse)
def ship_serial(
    serial_id: int,
    ship_data: SerialNumberShipDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Ship a serial number"""
    service = SerialNumberService(db)
    try:
        return service.ship_serial(serial_id, ship_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/serials/{serial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_serial(
    serial_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete serial number (soft delete)"""
    service = SerialNumberService(db)
    if not service.delete_serial(serial_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Serial {serial_id} not found")


# ==================== Traceability Link Endpoints ====================

@router.post("/links", response_model=TraceabilityLinkResponse, status_code=status.HTTP_201_CREATED)
def create_link(
    link_data: TraceabilityLinkCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new traceability link"""
    service = TraceabilityLinkService(db)
    return service.create_link(link_data)


@router.get("/links/{link_id}", response_model=TraceabilityLinkResponse)
def get_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get traceability link by ID"""
    service = TraceabilityLinkService(db)
    link = service.get_link(link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Link {link_id} not found")
    return link


@router.get("/links/by-parent-lot/{parent_lot_id}", response_model=List[TraceabilityLinkResponse])
def list_links_by_parent_lot(
    parent_lot_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List traceability links where lot is parent"""
    service = TraceabilityLinkService(db)
    return service.list_by_parent_lot(parent_lot_id)


@router.get("/links/by-child-lot/{child_lot_id}", response_model=List[TraceabilityLinkResponse])
def list_links_by_child_lot(
    child_lot_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List traceability links where lot is child"""
    service = TraceabilityLinkService(db)
    return service.list_by_child_lot(child_lot_id)


@router.get("/links/by-work-order/{work_order_id}", response_model=List[TraceabilityLinkResponse])
def list_links_by_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List traceability links for work order"""
    service = TraceabilityLinkService(db)
    return service.list_by_work_order(work_order_id)


# ==================== Genealogy Endpoints ====================

@router.post("/genealogy/history", response_model=List[GenealogyRecordResponse])
def query_genealogy_history(
    query_request: GenealogyQueryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Query genealogy history for an entity"""
    service = GenealogyService(db)
    return service.query_history(query_request)


@router.post("/genealogy/where-used", response_model=GenealogyTreeResponse)
def query_where_used(
    request: WhereUsedRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Build where-used tree (forward genealogy)"""
    service = GenealogyService(db)
    return service.build_where_used_tree(request)


@router.post("/genealogy/where-from", response_model=GenealogyTreeResponse)
def query_where_from(
    request: WhereFromRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Build where-from tree (reverse genealogy)"""
    service = GenealogyService(db)
    return service.build_where_from_tree(request)


# ==================== Recall Report Endpoint ====================

@router.post("/recall-reports", response_model=RecallReportResponse, status_code=status.HTTP_201_CREATED)
def generate_recall_report(
    request: RecallReportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a comprehensive recall report for affected lots.

    This endpoint performs forward genealogy tracing to identify:
    - All work orders that consumed the affected lots
    - All finished goods produced from those work orders
    - All shipments containing those finished goods
    - All customers who received the affected products

    The report includes:
    - Material and lot details
    - Total quantity affected
    - List of affected work orders with consumption details
    - List of affected shipments with customer information
    - Aggregated customer impact summary
    - Downstream impact statistics

    **Use Case**: Product recall, quality issue investigation, supply chain impact analysis

    **Authorization**: Requires authenticated user with traceability access

    **Example Request**:
    ```json
    {
        "material_id": 123,
        "lot_numbers": ["LOT-2024-001", "LOT-2024-002"],
        "reason": "Defective component detected in quality inspection",
        "severity": "HIGH",
        "include_customer_details": true,
        "include_distribution_chain": true
    }
    ```

    **Returns**: Comprehensive recall report with complete traceability data
    """
    service = RecallReportService(db)
    user_id = current_user.get("id", 0)
    organization_id = current_user.get("organization_id", 0)

    try:
        return service.generate_recall_report(request, user_id, organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating recall report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recall report: {str(e)}"
        )
