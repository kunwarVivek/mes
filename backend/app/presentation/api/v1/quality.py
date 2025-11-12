"""
API endpoints for Quality Management module.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.dtos.quality_dto import (
    NCRCreateDTO,
    NCRResponseDTO,
    NCRUpdateStatusDTO,
    InspectionPlanCreateDTO,
    InspectionPlanResponseDTO,
    InspectionLogCreateDTO,
    InspectionLogResponseDTO,
    FPYMetricsDTO,
    NCRDispositionDTO,
    NCRDispositionResponseDTO
)
from app.application.dtos.quality_enhancement_dto import (
    InspectionPlanCreateDTO as EnhancedInspectionPlanCreateDTO,
    InspectionPlanUpdateDTO as EnhancedInspectionPlanUpdateDTO,
    InspectionPlanApprovalDTO,
    InspectionPlanResponse as EnhancedInspectionPlanResponse,
    InspectionPointCreateDTO,
    InspectionPointUpdateDTO,
    InspectionPointResponse,
    InspectionCharacteristicCreateDTO,
    InspectionCharacteristicUpdateDTO,
    InspectionCharacteristicResponse,
    InspectionMeasurementCreateDTO,
    InspectionMeasurementBulkCreateDTO,
    InspectionMeasurementResponse,
    SPCAnalysisRequest,
    SPCAnalysisResponse,
    ControlChartDataRequest,
    ControlChartDataResponse,
    FPYCalculationRequest,
    FPYResponse
)
from app.application.services.quality_enhancement_service import (
    InspectionPlanService,
    InspectionPointService,
    InspectionCharacteristicService,
    InspectionMeasurementService,
    SPCAnalysisService,
    FPYCalculationService
)
from app.models.ncr import NCR, NCRStatus, DispositionType
from app.models.inspection import InspectionPlan, InspectionLog
from app.models.work_order import WorkOrder, OrderType, OrderStatus, WorkOrderOperation, WorkOrderMaterial
from app.models.inventory import Inventory, InventoryTransaction, TransactionType
from app.models.material import Material
from app.domain.entities.ncr import NCRDomain, NCRStatus as NCRStatusEnum
from app.domain.entities.inspection import InspectionPlanDomain, InspectionLogDomain, FPYCalculator
import logging

router = APIRouter(prefix="/quality", tags=["quality"])
logger = logging.getLogger(__name__)


@router.post("/ncrs", response_model=NCRResponseDTO, status_code=status.HTTP_201_CREATED)
def create_ncr(
    ncr_data: NCRCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new Non-Conformance Report (NCR).

    Args:
        ncr_data: NCR creation data
        db: Database session
        current_user: Authenticated user from JWT

    Returns:
        Created NCR entity

    Raises:
        HTTPException: If validation fails
    """
    organization_id = current_user.get("organization_id")
    plant_id = current_user.get("plant_id")

    if not organization_id or not plant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization and plant context required"
        )

    # Create domain entity for validation
    ncr_domain = NCRDomain(
        id=None,
        organization_id=organization_id,
        plant_id=plant_id,
        ncr_number=ncr_data.ncr_number,
        work_order_id=ncr_data.work_order_id,
        material_id=ncr_data.material_id,
        defect_type=ncr_data.defect_type.value,
        defect_description=ncr_data.defect_description,
        quantity_defective=ncr_data.quantity_defective,
        status=NCRStatusEnum.OPEN,
        reported_by_user_id=ncr_data.reported_by_user_id,
        attachment_urls=ncr_data.attachment_urls
    )

    # Create database model
    ncr_db = NCR(
        organization_id=organization_id,
        plant_id=plant_id,
        ncr_number=ncr_domain.ncr_number,
        work_order_id=ncr_domain.work_order_id,
        material_id=ncr_domain.material_id,
        defect_type=ncr_domain.defect_type,
        defect_description=ncr_domain.defect_description,
        quantity_defective=ncr_domain.quantity_defective,
        status=NCRStatus.OPEN,
        reported_by_user_id=ncr_domain.reported_by_user_id,
        attachment_urls=ncr_domain.attachment_urls
    )

    db.add(ncr_db)
    db.commit()
    db.refresh(ncr_db)

    return ncr_db


@router.get("/ncrs", response_model=List[NCRResponseDTO])
def list_ncrs(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    work_order_id: Optional[int] = Query(None, description="Filter by work order"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List NCRs with optional filtering.

    Args:
        status_filter: Filter by NCR status
        work_order_id: Filter by work order ID
        skip: Pagination offset
        limit: Pagination limit
        db: Database session
        current_user: Authenticated user from JWT

    Returns:
        List of NCRs
    """
    query = db.query(NCR)

    if status_filter:
        query = query.filter(NCR.status == status_filter)

    if work_order_id:
        query = query.filter(NCR.work_order_id == work_order_id)

    query = query.order_by(NCR.created_at.desc())
    ncrs = query.offset(skip).limit(limit).all()

    return ncrs


@router.patch("/ncrs/{ncr_id}/status", response_model=NCRResponseDTO)
def update_ncr_status(
    ncr_id: int,
    status_data: NCRUpdateStatusDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update NCR status following workflow.

    Args:
        ncr_id: NCR ID
        status_data: New status data
        db: Database session
        current_user: Authenticated user from JWT

    Returns:
        Updated NCR

    Raises:
        HTTPException: If NCR not found or invalid transition
    """
    ncr_db = db.query(NCR).filter(NCR.id == ncr_id).first()

    if not ncr_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NCR with id {ncr_id} not found"
        )

    # Load domain entity to enforce workflow
    ncr_domain = NCRDomain(
        id=ncr_db.id,
        organization_id=ncr_db.organization_id,
        plant_id=ncr_db.plant_id,
        ncr_number=ncr_db.ncr_number,
        work_order_id=ncr_db.work_order_id,
        material_id=ncr_db.material_id,
        defect_type=ncr_db.defect_type.value,
        defect_description=ncr_db.defect_description,
        quantity_defective=ncr_db.quantity_defective,
        status=NCRStatusEnum(ncr_db.status.value),
        reported_by_user_id=ncr_db.reported_by_user_id,
        attachment_urls=ncr_db.attachment_urls or [],
        resolution_notes=ncr_db.resolution_notes
    )

    try:
        # Apply workflow transition
        if status_data.status == NCRStatusEnum.IN_REVIEW:
            ncr_domain.move_to_review()
        elif status_data.status == NCRStatusEnum.RESOLVED:
            ncr_domain.resolve(
                status_data.resolution_notes,
                status_data.resolved_by_user_id or current_user.get("id")
            )
        elif status_data.status == NCRStatusEnum.CLOSED:
            ncr_domain.close()

        # Update database model
        ncr_db.status = NCRStatus(ncr_domain.status.value)
        if ncr_domain.resolution_notes:
            ncr_db.resolution_notes = ncr_domain.resolution_notes
            ncr_db.resolved_by_user_id = ncr_domain._resolved_by_user_id
            ncr_db.resolved_at = ncr_domain._resolved_at

        db.commit()
        db.refresh(ncr_db)

        return ncr_db

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/inspection-plans", response_model=InspectionPlanResponseDTO, status_code=status.HTTP_201_CREATED)
def create_inspection_plan(
    plan_data: InspectionPlanCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new Inspection Plan.

    Args:
        plan_data: Inspection plan creation data
        db: Database session
        current_user: Authenticated user from JWT

    Returns:
        Created inspection plan
    """
    organization_id = current_user.get("organization_id")
    plant_id = current_user.get("plant_id")

    if not organization_id or not plant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization and plant context required"
        )

    # Create domain entity for validation
    plan_domain = InspectionPlanDomain(
        id=None,
        organization_id=organization_id,
        plant_id=plant_id,
        plan_name=plan_data.plan_name,
        material_id=plan_data.material_id,
        inspection_frequency=plan_data.inspection_frequency.value,
        sample_size=plan_data.sample_size,
        is_active=True
    )

    # Convert characteristics to JSON
    characteristics_json = None
    if plan_data.characteristics:
        characteristics_json = [char.dict() for char in plan_data.characteristics]

    # Create database model
    plan_db = InspectionPlan(
        organization_id=organization_id,
        plant_id=plant_id,
        plan_name=plan_domain.plan_name,
        material_id=plan_domain.material_id,
        inspection_frequency=plan_domain.inspection_frequency,
        sample_size=plan_domain.sample_size,
        characteristics=characteristics_json,
        is_active=True
    )

    db.add(plan_db)
    db.commit()
    db.refresh(plan_db)

    return plan_db


@router.post("/inspections", response_model=InspectionLogResponseDTO, status_code=status.HTTP_201_CREATED)
def create_inspection_log(
    log_data: InspectionLogCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new Inspection Log.

    Args:
        log_data: Inspection log creation data
        db: Database session
        current_user: Authenticated user from JWT

    Returns:
        Created inspection log
    """
    organization_id = current_user.get("organization_id")
    plant_id = current_user.get("plant_id")

    if not organization_id or not plant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization and plant context required"
        )

    # Create domain entity for validation
    log_domain = InspectionLogDomain(
        id=None,
        organization_id=organization_id,
        plant_id=plant_id,
        inspection_plan_id=log_data.inspection_plan_id,
        work_order_id=log_data.work_order_id,
        inspected_quantity=log_data.inspected_quantity,
        passed_quantity=log_data.passed_quantity,
        failed_quantity=log_data.failed_quantity,
        inspector_user_id=log_data.inspector_user_id,
        inspection_notes=log_data.inspection_notes
    )

    # Create database model
    log_db = InspectionLog(
        organization_id=organization_id,
        plant_id=plant_id,
        inspection_plan_id=log_domain.inspection_plan_id,
        work_order_id=log_domain.work_order_id,
        inspected_quantity=log_domain.inspected_quantity,
        passed_quantity=log_domain.passed_quantity,
        failed_quantity=log_domain.failed_quantity,
        inspector_user_id=log_domain.inspector_user_id,
        inspection_notes=log_domain.inspection_notes,
        measurement_data=log_data.measurement_data
    )

    db.add(log_db)
    db.commit()
    db.refresh(log_db)

    return log_db


@router.get("/fpy", response_model=FPYMetricsDTO)
def get_fpy_metrics(
    work_order_id: Optional[int] = Query(None, description="Filter by work order"),
    days: int = Query(30, ge=1, le=365, description="Number of days for rolling FPY"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get First Pass Yield (FPY) metrics.

    Args:
        work_order_id: Optional work order filter
        days: Number of days for rolling calculation
        db: Database session
        current_user: Authenticated user from JWT

    Returns:
        FPY metrics
    """
    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()

    query = db.query(InspectionLog).filter(
        InspectionLog.inspected_at >= period_start
    )

    if work_order_id:
        query = query.filter(InspectionLog.work_order_id == work_order_id)

    inspection_logs = query.all()

    # Calculate FPY using domain logic
    total_inspected = sum(log.inspected_quantity for log in inspection_logs)
    total_passed = sum(log.passed_quantity for log in inspection_logs)
    total_failed = sum(log.failed_quantity for log in inspection_logs)

    if total_inspected == 0:
        fpy_percentage = 0.0
    else:
        fpy = FPYCalculator.calculate_fpy(total_inspected, total_passed)
        fpy_percentage = fpy * 100

    return FPYMetricsDTO(
        total_inspected=total_inspected,
        total_passed=total_passed,
        total_failed=total_failed,
        fpy_percentage=fpy_percentage,
        period_start=period_start,
        period_end=period_end
    )


# ==================== Enhanced Quality Management Endpoints ====================

# Inspection Plans (Enhanced)
@router.post("/v2/inspection-plans", response_model=EnhancedInspectionPlanResponse, status_code=status.HTTP_201_CREATED)
def create_enhanced_inspection_plan(
    plan_data: EnhancedInspectionPlanCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new enhanced inspection plan with SPC support"""
    service = InspectionPlanService(db)
    try:
        plan = service.create_plan(plan_data)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/v2/inspection-plans", response_model=List[EnhancedInspectionPlanResponse])
def list_enhanced_inspection_plans(
    organization_id: int = Query(..., gt=0),
    plan_type: Optional[str] = Query(None),
    plant_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List enhanced inspection plans"""
    service = InspectionPlanService(db)
    return service.list_plans(organization_id, skip, limit, plan_type, plant_id, active_only)


@router.get("/v2/inspection-plans/{plan_id}", response_model=EnhancedInspectionPlanResponse)
def get_enhanced_inspection_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get enhanced inspection plan by ID"""
    service = InspectionPlanService(db)
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")
    return plan


@router.patch("/v2/inspection-plans/{plan_id}", response_model=EnhancedInspectionPlanResponse)
def update_enhanced_inspection_plan(
    plan_id: int,
    plan_data: EnhancedInspectionPlanUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update enhanced inspection plan"""
    service = InspectionPlanService(db)
    plan = service.update_plan(plan_id, plan_data)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")
    return plan


@router.post("/v2/inspection-plans/{plan_id}/approve", response_model=EnhancedInspectionPlanResponse)
def approve_inspection_plan(
    plan_id: int,
    approval_data: InspectionPlanApprovalDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve an inspection plan"""
    service = InspectionPlanService(db)
    plan = service.approve_plan(plan_id, approval_data)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")
    return plan


@router.delete("/v2/inspection-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inspection_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete inspection plan (soft delete)"""
    service = InspectionPlanService(db)
    if not service.delete_plan(plan_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")


# Inspection Points
@router.post("/v2/inspection-points", response_model=InspectionPointResponse, status_code=status.HTTP_201_CREATED)
def create_inspection_point(
    point_data: InspectionPointCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new inspection point"""
    service = InspectionPointService(db)
    return service.create_point(point_data)


@router.get("/v2/inspection-points", response_model=List[InspectionPointResponse])
def list_inspection_points(
    inspection_plan_id: int = Query(..., gt=0),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List inspection points for a plan"""
    service = InspectionPointService(db)
    return service.list_by_plan(inspection_plan_id, skip, limit, active_only)


@router.get("/v2/inspection-points/{point_id}", response_model=InspectionPointResponse)
def get_inspection_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get inspection point by ID"""
    service = InspectionPointService(db)
    point = service.get_point(point_id)
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Point {point_id} not found")
    return point


@router.patch("/v2/inspection-points/{point_id}", response_model=InspectionPointResponse)
def update_inspection_point(
    point_id: int,
    point_data: InspectionPointUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update inspection point"""
    service = InspectionPointService(db)
    point = service.update_point(point_id, point_data)
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Point {point_id} not found")
    return point


# Inspection Characteristics
@router.post("/v2/inspection-characteristics", response_model=InspectionCharacteristicResponse, status_code=status.HTTP_201_CREATED)
def create_inspection_characteristic(
    char_data: InspectionCharacteristicCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new inspection characteristic"""
    service = InspectionCharacteristicService(db)
    return service.create_characteristic(char_data)


@router.get("/v2/inspection-characteristics", response_model=List[InspectionCharacteristicResponse])
def list_inspection_characteristics(
    inspection_point_id: int = Query(..., gt=0),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List inspection characteristics for a point"""
    service = InspectionCharacteristicService(db)
    return service.list_by_point(inspection_point_id, skip, limit, active_only)


@router.get("/v2/inspection-characteristics/{char_id}", response_model=InspectionCharacteristicResponse)
def get_inspection_characteristic(
    char_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get inspection characteristic by ID"""
    service = InspectionCharacteristicService(db)
    char = service.get_characteristic(char_id)
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Characteristic {char_id} not found")
    return char


@router.patch("/v2/inspection-characteristics/{char_id}", response_model=InspectionCharacteristicResponse)
def update_inspection_characteristic(
    char_id: int,
    char_data: InspectionCharacteristicUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update inspection characteristic"""
    service = InspectionCharacteristicService(db)
    char = service.update_characteristic(char_id, char_data)
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Characteristic {char_id} not found")
    return char


@router.post("/v2/inspection-characteristics/{char_id}/recalculate-limits", response_model=InspectionCharacteristicResponse)
def recalculate_control_limits(
    char_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Recalculate control limits based on recent measurements"""
    service = InspectionCharacteristicService(db)
    char = service.recalculate_control_limits(char_id)
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Characteristic {char_id} not found")
    return char


# Inspection Measurements
@router.post("/v2/measurements", response_model=InspectionMeasurementResponse, status_code=status.HTTP_201_CREATED)
def record_measurement(
    measurement_data: InspectionMeasurementCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record a new inspection measurement"""
    service = InspectionMeasurementService(db)
    try:
        return service.record_measurement(measurement_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/v2/measurements/bulk", response_model=List[InspectionMeasurementResponse], status_code=status.HTTP_201_CREATED)
def record_bulk_measurements(
    bulk_data: InspectionMeasurementBulkCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record multiple measurements at once"""
    service = InspectionMeasurementService(db)
    try:
        return service.record_bulk_measurements(bulk_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/v2/measurements", response_model=List[InspectionMeasurementResponse])
def list_measurements(
    characteristic_id: Optional[int] = Query(None),
    work_order_id: Optional[int] = Query(None),
    lot_number: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List inspection measurements with filters"""
    service = InspectionMeasurementService(db)

    if characteristic_id:
        return service.list_by_characteristic(characteristic_id, skip, limit, start_date, end_date)
    elif work_order_id:
        return service.list_by_work_order(work_order_id, skip, limit)
    elif lot_number and organization_id:
        return service.list_by_lot(lot_number, organization_id, skip, limit)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide characteristic_id, work_order_id, or lot_number+organization_id"
        )


# SPC Analysis
@router.post("/v2/spc/analyze", response_model=SPCAnalysisResponse)
def analyze_spc(
    analysis_request: SPCAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Perform SPC analysis on a characteristic"""
    service = SPCAnalysisService(db)
    try:
        return service.analyze_characteristic(analysis_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/v2/spc/control-chart", response_model=ControlChartDataResponse)
def get_control_chart_data(
    chart_request: ControlChartDataRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get control chart data for visualization"""
    service = SPCAnalysisService(db)
    try:
        return service.get_control_chart_data(chart_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Enhanced FPY Calculation
@router.post("/v2/fpy/calculate", response_model=FPYResponse)
def calculate_fpy_v2(
    fpy_request: FPYCalculationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate enhanced First Pass Yield with detailed breakdowns"""
    service = FPYCalculationService(db)
    return service.calculate_fpy(fpy_request)


# ==================== NCR Disposition Workflow ====================

@router.post("/ncr-reports/{ncr_id}/disposition", response_model=NCRDispositionResponseDTO)
def disposition_ncr(
    ncr_id: int,
    disposition_data: NCRDispositionDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Perform disposition action on an NCR.

    Implements disposition workflow per FRD_QUALITY.md lines 26-51.

    Args:
        ncr_id: NCR ID
        disposition_data: Disposition type and details
        db: Database session
        current_user: Authenticated user from JWT

    Returns:
        NCRDispositionResponseDTO: Disposition details and actions taken

    Raises:
        HTTPException: If NCR not found, already dispositioned, or action fails
    """
    try:
        # Get NCR
        ncr = db.query(NCR).filter(NCR.id == ncr_id).first()
        if not ncr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"NCR with id {ncr_id} not found"
            )

        # Check if already dispositioned
        if ncr.disposition_type is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NCR {ncr.ncr_number} has already been dispositioned as {ncr.disposition_type.value}"
            )

        # Get user ID
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User ID required"
            )

        # Track actions taken
        actions_taken = []

        # Response data
        response_data = {
            "ncr_id": ncr.id,
            "ncr_number": ncr.ncr_number,
            "disposition_type": disposition_data.disposition_type.value,
            "disposition_by_user_id": user_id,
            "actions_taken": actions_taken
        }

        # Get parent work order for reference
        parent_work_order = db.query(WorkOrder).filter(WorkOrder.id == ncr.work_order_id).first()
        if not parent_work_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent work order {ncr.work_order_id} not found"
            )

        # Get material for reference
        material = db.query(Material).filter(Material.id == ncr.material_id).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material {ncr.material_id} not found"
            )

        logger.info(
            f"Processing NCR disposition: ncr_id={ncr_id}, "
            f"type={disposition_data.disposition_type.value}, user={user_id}"
        )

        # ==================== REWORK Disposition ====================
        if disposition_data.disposition_type == DispositionType.REWORK:
            # Generate rework work order number
            rework_wo_number = f"{parent_work_order.work_order_number}-RW-{ncr.ncr_number}"

            # Create rework work order
            rework_order = WorkOrder(
                organization_id=ncr.organization_id,
                plant_id=ncr.plant_id,
                work_order_number=rework_wo_number,
                material_id=ncr.material_id,
                order_type=OrderType.REWORK,
                order_status=OrderStatus.PLANNED,
                planned_quantity=ncr.quantity_defective,
                is_rework_order=True,
                parent_work_order_id=ncr.work_order_id,
                rework_reason_code=ncr.ncr_number,
                created_by_user_id=user_id
            )
            db.add(rework_order)
            db.flush()  # Get ID for logging

            actions_taken.append(f"Created rework work order: {rework_wo_number}")
            logger.info(f"Created rework work order {rework_wo_number} for NCR {ncr.ncr_number}")

            # Copy operations from parent work order
            parent_operations = db.query(WorkOrderOperation).filter(
                WorkOrderOperation.work_order_id == parent_work_order.id
            ).order_by(WorkOrderOperation.operation_number).all()

            for parent_op in parent_operations:
                rework_op = WorkOrderOperation(
                    organization_id=ncr.organization_id,
                    plant_id=ncr.plant_id,
                    work_order_id=rework_order.id,
                    operation_number=parent_op.operation_number,
                    operation_name=f"REWORK: {parent_op.operation_name}",
                    work_center_id=parent_op.work_center_id,
                    setup_time_minutes=parent_op.setup_time_minutes,
                    run_time_per_unit_minutes=parent_op.run_time_per_unit_minutes,
                    status=parent_op.status,
                    scheduling_mode=parent_op.scheduling_mode
                )
                db.add(rework_op)

            if parent_operations:
                actions_taken.append(f"Copied {len(parent_operations)} operations from parent work order")

            # Copy materials from parent work order
            parent_materials = db.query(WorkOrderMaterial).filter(
                WorkOrderMaterial.work_order_id == parent_work_order.id
            ).all()

            for parent_mat in parent_materials:
                # Scale material quantity based on rework quantity vs parent quantity
                scale_factor = ncr.quantity_defective / parent_work_order.planned_quantity
                rework_mat = WorkOrderMaterial(
                    work_order_id=rework_order.id,
                    material_id=parent_mat.material_id,
                    planned_quantity=parent_mat.planned_quantity * scale_factor,
                    unit_of_measure_id=parent_mat.unit_of_measure_id,
                    backflush=parent_mat.backflush
                )
                db.add(rework_mat)

            if parent_materials:
                actions_taken.append(f"Copied {len(parent_materials)} material requirements")

            # Calculate estimated rework cost
            # Material cost estimate (simplified)
            material_cost_estimate = sum(
                parent_mat.planned_quantity * (ncr.quantity_defective / parent_work_order.planned_quantity)
                for parent_mat in parent_materials
            ) * 10  # Rough estimate: $10 per unit material

            # Labor cost estimate (simplified)
            labor_cost_estimate = sum(
                op.run_time_per_unit_minutes * ncr.quantity_defective / 60  # Convert to hours
                for op in parent_operations
            ) * 25  # $25/hour labor rate

            rework_cost = material_cost_estimate + labor_cost_estimate
            ncr.rework_cost = rework_cost

            actions_taken.append(f"Calculated rework cost estimate: ${rework_cost:.2f}")
            logger.info(f"Rework cost estimated at ${rework_cost:.2f} for NCR {ncr.ncr_number}")

            response_data["rework_work_order_id"] = rework_order.id
            response_data["rework_cost"] = rework_cost

        # ==================== SCRAP Disposition ====================
        elif disposition_data.disposition_type == DispositionType.SCRAP:
            # Find inventory record for this material at the plant
            inventory_records = db.query(Inventory).filter(
                Inventory.organization_id == ncr.organization_id,
                Inventory.plant_id == ncr.plant_id,
                Inventory.material_id == ncr.material_id,
                Inventory.quantity_on_hand >= ncr.quantity_defective
            ).all()

            if not inventory_records:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient inventory for material {material.material_number} to scrap {ncr.quantity_defective} units"
                )

            # Use first available inventory record (FIFO logic)
            inventory = inventory_records[0]

            # Calculate scrap cost
            # Try to get current average cost from material or use a default
            unit_cost = getattr(material, 'current_average_cost', 0) or 50.0  # Default $50 if not available
            scrap_cost = ncr.quantity_defective * unit_cost
            ncr.scrap_cost = scrap_cost

            # Adjust inventory - reduce on_hand_quantity
            old_quantity = inventory.quantity_on_hand
            inventory.quantity_on_hand -= ncr.quantity_defective
            inventory.last_movement_date = datetime.utcnow()

            actions_taken.append(
                f"Adjusted inventory: reduced {material.material_number} from {old_quantity} to {inventory.quantity_on_hand}"
            )
            logger.info(
                f"Inventory adjustment for scrap: material={material.material_number}, "
                f"qty={ncr.quantity_defective}, cost=${scrap_cost:.2f}"
            )

            # Create inventory transaction for audit trail
            scrap_transaction = InventoryTransaction(
                organization_id=ncr.organization_id,
                plant_id=ncr.plant_id,
                material_id=ncr.material_id,
                storage_location_id=inventory.storage_location_id,
                transaction_type=TransactionType.ADJUSTMENT,
                transaction_reference=f"NCR-SCRAP-{ncr.ncr_number}",
                batch_number=inventory.batch_number,
                quantity=-ncr.quantity_defective,  # Negative for scrap
                unit_of_measure_id=inventory.unit_of_measure_id,
                unit_cost=unit_cost,
                total_value=-scrap_cost,  # Negative for cost write-off
                transaction_date=datetime.utcnow(),
                posted_by_user_id=user_id,
                notes=f"Scrap disposition for NCR {ncr.ncr_number}: {disposition_data.notes or 'No notes'}"
            )
            db.add(scrap_transaction)

            actions_taken.append(f"Created scrap transaction audit log: ${scrap_cost:.2f}")
            actions_taken.append(f"Calculated scrap cost: ${scrap_cost:.2f}")

            response_data["scrap_cost"] = scrap_cost
            response_data["inventory_adjusted"] = True

        # ==================== USE_AS_IS Disposition ====================
        elif disposition_data.disposition_type == DispositionType.USE_AS_IS:
            # Check if customer is affected
            if ncr.customer_affected:
                # Log notification (since we don't have a notifications table yet)
                logger.warning(
                    f"CUSTOMER NOTIFICATION REQUIRED: NCR {ncr.ncr_number} - "
                    f"Material {material.material_number} approved for use-as-is. "
                    f"Customer must be notified of deviation."
                )
                actions_taken.append("Customer notification logged (requires manual follow-up)")
                response_data["customer_notified"] = True
            else:
                actions_taken.append("No customer notification required (internal use)")
                response_data["customer_notified"] = False

            # Log deviation approval
            logger.info(
                f"USE-AS-IS approved for NCR {ncr.ncr_number}: "
                f"Material {material.material_number}, Qty {ncr.quantity_defective}"
            )
            actions_taken.append("Deviation approved - material accepted as-is")

        # ==================== RETURN_TO_SUPPLIER Disposition ====================
        elif disposition_data.disposition_type == DispositionType.RETURN_TO_SUPPLIER:
            # Calculate return cost
            unit_cost = getattr(material, 'unit_cost', 0) or getattr(material, 'current_average_cost', 0) or 50.0
            return_cost = ncr.quantity_defective * unit_cost

            # Log return shipment creation (since we don't have a shipments table)
            logger.info(
                f"RETURN TO SUPPLIER: NCR {ncr.ncr_number} - "
                f"Material {material.material_number}, Qty {ncr.quantity_defective}, "
                f"Return cost ${return_cost:.2f}"
            )
            actions_taken.append(
                f"Return shipment logged for {ncr.quantity_defective} units (requires manual creation)"
            )
            actions_taken.append(f"Return cost for supplier credit: ${return_cost:.2f}")

            response_data["return_shipment_created"] = True

        # ==================== Update NCR with Disposition ====================
        ncr.disposition_type = DispositionType(disposition_data.disposition_type.value)
        ncr.disposition_date = datetime.utcnow()
        ncr.disposition_by_user_id = user_id
        ncr.status = NCRStatus.RESOLVED

        if disposition_data.root_cause:
            ncr.root_cause = disposition_data.root_cause
            actions_taken.append("Root cause documented")

        if disposition_data.notes:
            ncr.resolution_notes = (ncr.resolution_notes or "") + f"\nDisposition notes: {disposition_data.notes}"

        # Commit transaction
        db.commit()
        db.refresh(ncr)

        logger.info(
            f"NCR disposition completed: ncr_id={ncr_id}, "
            f"type={disposition_data.disposition_type.value}, "
            f"status=RESOLVED, actions_count={len(actions_taken)}"
        )

        # Build response
        response_data["disposition_date"] = ncr.disposition_date
        response_data["actions_taken"] = actions_taken

        return NCRDispositionResponseDTO(**response_data)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing NCR disposition: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process disposition: {str(e)}"
        )
