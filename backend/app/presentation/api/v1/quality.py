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
