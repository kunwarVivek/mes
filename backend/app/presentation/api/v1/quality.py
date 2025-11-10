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
    FPYMetricsDTO
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
from app.models.ncr import NCR, NCRStatus
from app.models.inspection import InspectionPlan, InspectionLog
from app.domain.entities.ncr import NCRDomain, NCRStatus as NCRStatusEnum
from app.domain.entities.inspection import InspectionPlanDomain, InspectionLogDomain, FPYCalculator

router = APIRouter(prefix="/quality", tags=["quality"])


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
