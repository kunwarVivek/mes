"""
API endpoints for Quality Management module.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import statistics

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
    FPYResponse,
    # Nested DTOs for simplified API
    NestedInspectionPlanCreateDTO,
    NestedInspectionPlanResponse,
    InspectionPlanUpdateNestedDTO,
    InspectionLogCreateNestedDTO,
    InspectionLogResponse,
    InspectionLogMeasurementResponse,
    NestedPointResponse,
    NestedCharacteristicResponse,
    # SPC Chart DTOs
    SPCChartResponse,
    SPCDataPoint
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


# ==================== Inspection Plans CRUD API ====================

@router.post("/inspection-plans", response_model=NestedInspectionPlanResponse, status_code=status.HTTP_201_CREATED)
def create_inspection_plan_nested(
    plan_data: NestedInspectionPlanCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new Inspection Plan with nested inspection points and characteristics.

    This endpoint creates:
    - An inspection plan
    - Multiple inspection points (optional)
    - Multiple characteristics per point (optional)

    All in a single transaction.

    Args:
        plan_data: Nested plan creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created inspection plan with all nested data

    Raises:
        HTTPException: If validation fails or creation errors occur
    """
    try:
        organization_id = current_user.get("organization_id")
        plant_id = current_user.get("plant_id")
        user_id = current_user.get("id")

        if not organization_id or not user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization context and user ID required"
            )

        # Generate plan code from name
        plan_code = plan_data.name.upper().replace(" ", "_")[:50]

        # Create the inspection plan
        from app.models.quality_enhancement import InspectionPlan
        plan = InspectionPlan(
            organization_id=organization_id,
            plant_id=plant_id,
            plan_code=plan_code,
            plan_name=plan_data.name,
            description=plan_data.description,
            plan_type=plan_data.plan_type,
            applies_to=plan_data.applies_to,
            material_id=plan_data.material_id,
            work_center_id=plan_data.work_center_id,
            frequency=plan_data.frequency,
            frequency_value=plan_data.frequency_value,
            sample_size=plan_data.sample_size,
            spc_enabled=plan_data.spc_enabled,
            control_limits_config=plan_data.control_limits_config,
            effective_date=plan_data.effective_date,
            expiry_date=plan_data.expiry_date,
            instructions=plan_data.instructions,
            acceptance_criteria=plan_data.acceptance_criteria,
            is_active=True,
            revision=1,
            created_by=user_id
        )

        db.add(plan)
        db.flush()  # Get plan ID

        logger.info(f"Created inspection plan: id={plan.id}, code={plan.plan_code}")

        # Create inspection points
        from app.models.quality_enhancement import InspectionPoint, InspectionCharacteristic

        for point_data in plan_data.inspection_points:
            point = InspectionPoint(
                organization_id=organization_id,
                inspection_plan_id=plan.id,
                point_code=point_data.point_code,
                point_name=point_data.point_name,
                description=point_data.description,
                inspection_method=point_data.inspection_method,
                inspection_equipment=point_data.inspection_equipment,
                sequence=point_data.sequence,
                is_mandatory=point_data.is_mandatory,
                is_critical=point_data.is_critical,
                inspection_instructions=point_data.inspection_instructions,
                acceptance_criteria=point_data.acceptance_criteria,
                is_active=True
            )

            db.add(point)
            db.flush()  # Get point ID

            logger.info(f"Created inspection point: id={point.id}, code={point.point_code}")

            # Create characteristics for this point
            for char_data in point_data.characteristics:
                characteristic = InspectionCharacteristic(
                    organization_id=organization_id,
                    inspection_point_id=point.id,
                    characteristic_code=char_data.characteristic_code,
                    characteristic_name=char_data.characteristic_name,
                    description=char_data.description,
                    characteristic_type=char_data.characteristic_type,
                    data_type=char_data.data_type,
                    unit_of_measure=char_data.unit_of_measure,
                    target_value=char_data.target_value,
                    lower_spec_limit=char_data.lower_spec_limit,
                    upper_spec_limit=char_data.upper_spec_limit,
                    lower_control_limit=char_data.lower_control_limit,
                    upper_control_limit=char_data.upper_control_limit,
                    track_spc=char_data.track_spc,
                    control_chart_type=char_data.control_chart_type,
                    subgroup_size=char_data.subgroup_size,
                    allowed_values=char_data.allowed_values,
                    tolerance_type=char_data.tolerance_type,
                    tolerance=char_data.tolerance,
                    sequence=char_data.sequence,
                    is_active=True
                )

                db.add(characteristic)
                logger.info(f"Created characteristic: code={characteristic.characteristic_code}")

        db.commit()
        db.refresh(plan)

        logger.info(f"Inspection plan creation completed: plan_id={plan.id}, points={len(plan_data.inspection_points)}")

        # Build nested response
        return _build_nested_plan_response(plan, db)

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating inspection plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inspection plan: {str(e)}"
        )


@router.get("/inspection-plans/{plan_id}", response_model=NestedInspectionPlanResponse)
def get_inspection_plan_nested(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get an Inspection Plan with all nested points and characteristics.

    Args:
        plan_id: Inspection plan ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Full inspection plan with all nested data

    Raises:
        HTTPException: If plan not found
    """
    from app.models.quality_enhancement import InspectionPlan

    plan = db.query(InspectionPlan).filter(InspectionPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection plan with id {plan_id} not found"
        )

    return _build_nested_plan_response(plan, db)


@router.get("/inspection-plans", response_model=List[NestedInspectionPlanResponse])
def list_inspection_plans_nested(
    plan_type: Optional[str] = Query(None, description="Filter by plan type"),
    applies_to: Optional[str] = Query(None, description="Filter by applies_to"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    material_id: Optional[int] = Query(None, description="Filter by material ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List Inspection Plans with optional filtering.

    Args:
        plan_type: Filter by plan type (INCOMING, IN_PROCESS, FINAL, FIRST_ARTICLE, AUDIT)
        applies_to: Filter by scope (MATERIAL, WORK_ORDER, PRODUCT, PROCESS)
        is_active: Filter by active status
        material_id: Filter by material ID
        skip: Pagination offset
        limit: Pagination limit
        db: Database session
        current_user: Authenticated user

    Returns:
        List of inspection plans
    """
    from app.models.quality_enhancement import InspectionPlan

    organization_id = current_user.get("organization_id")

    query = db.query(InspectionPlan).filter(
        InspectionPlan.organization_id == organization_id
    )

    if plan_type:
        query = query.filter(InspectionPlan.plan_type == plan_type)

    if applies_to:
        query = query.filter(InspectionPlan.applies_to == applies_to)

    if is_active is not None:
        query = query.filter(InspectionPlan.is_active == is_active)

    if material_id:
        query = query.filter(InspectionPlan.material_id == material_id)

    query = query.order_by(InspectionPlan.created_at.desc())
    plans = query.offset(skip).limit(limit).all()

    return [_build_nested_plan_response(plan, db) for plan in plans]


@router.put("/inspection-plans/{plan_id}", response_model=NestedInspectionPlanResponse)
def update_inspection_plan_nested(
    plan_id: int,
    plan_data: InspectionPlanUpdateNestedDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an Inspection Plan.

    Note: This endpoint updates plan-level fields only.
    To add/update/delete points and characteristics, use the dedicated endpoints.

    Args:
        plan_id: Inspection plan ID
        plan_data: Update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated inspection plan

    Raises:
        HTTPException: If plan not found
    """
    from app.models.quality_enhancement import InspectionPlan

    plan = db.query(InspectionPlan).filter(InspectionPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection plan with id {plan_id} not found"
        )

    try:
        # Update fields
        update_data = plan_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            if field == "name":
                setattr(plan, "plan_name", value)
            elif hasattr(plan, field):
                setattr(plan, field, value)

        db.commit()
        db.refresh(plan)

        logger.info(f"Updated inspection plan: id={plan_id}")

        return _build_nested_plan_response(plan, db)

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating inspection plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update inspection plan: {str(e)}"
        )


@router.delete("/inspection-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inspection_plan_nested(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an Inspection Plan (soft delete - sets is_active = False).

    Args:
        plan_id: Inspection plan ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If plan not found
    """
    from app.models.quality_enhancement import InspectionPlan

    plan = db.query(InspectionPlan).filter(InspectionPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection plan with id {plan_id} not found"
        )

    try:
        plan.is_active = False
        db.commit()

        logger.info(f"Soft deleted inspection plan: id={plan_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting inspection plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete inspection plan: {str(e)}"
        )


@router.post("/inspection-logs", response_model=InspectionLogResponse, status_code=status.HTTP_201_CREATED)
def log_inspection_results(
    log_data: InspectionLogCreateNestedDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Log Inspection Results with measurements.

    This endpoint:
    1. Validates measurements against characteristic limits (LSL/USL)
    2. Records all measurements
    3. Determines overall inspection status (PASS/FAIL)
    4. Returns detailed results

    Args:
        log_data: Inspection log data with measurements
        db: Database session
        current_user: Authenticated user

    Returns:
        Inspection log with results

    Raises:
        HTTPException: If validation fails
    """
    try:
        organization_id = current_user.get("organization_id")

        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization context required"
            )

        # Get the inspection plan
        from app.models.quality_enhancement import InspectionPlan, InspectionCharacteristic, InspectionMeasurement

        plan = db.query(InspectionPlan).filter(
            InspectionPlan.id == log_data.inspection_plan_id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inspection plan with id {log_data.inspection_plan_id} not found"
            )

        logger.info(f"Logging inspection results for plan: {plan.plan_name}")

        # Track results
        measurement_records = []
        conforming_count = 0
        non_conforming_count = 0
        out_of_control_count = 0

        # Process each measurement
        for measurement_data in log_data.measurements:
            # Get characteristic
            characteristic = db.query(InspectionCharacteristic).filter(
                InspectionCharacteristic.id == measurement_data.characteristic_id
            ).first()

            if not characteristic:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Characteristic with id {measurement_data.characteristic_id} not found"
                )

            # Create measurement record
            measurement = InspectionMeasurement(
                organization_id=organization_id,
                characteristic_id=characteristic.id,
                inspection_plan_id=plan.id,
                work_order_id=log_data.work_order_id,
                material_id=log_data.material_id,
                lot_number=log_data.lot_number,
                serial_number=log_data.serial_number,
                measured_value=measurement_data.measured_value,
                measured_text=measurement_data.measured_text,
                sample_number=measurement_data.sample_number,
                measured_by=log_data.inspected_by_user_id,
                measurement_timestamp=datetime.now(timezone.utc),
                inspection_equipment_id=log_data.inspection_equipment_id,
                environmental_conditions=log_data.environmental_conditions,
                notes=measurement_data.notes
            )

            # Validate measurement against limits
            if characteristic.characteristic_type == 'VARIABLE' and measurement_data.measured_value is not None:
                measured_val = float(measurement_data.measured_value)

                # Check spec limits
                measurement.is_conforming = characteristic.is_within_spec(measured_val)

                # Calculate deviation from target
                if characteristic.target_value:
                    measurement.deviation = measurement.calculate_deviation(float(characteristic.target_value))

                # Check control limits for SPC
                if characteristic.track_spc:
                    is_within_control = characteristic.is_within_control_limits(measured_val)
                    measurement.is_out_of_control = not is_within_control

                    if measurement.is_out_of_control:
                        out_of_control_count += 1
                        measurement.control_violation_type = "OUT_OF_LIMITS"
                        logger.warning(
                            f"Out of control measurement: char={characteristic.characteristic_name}, "
                            f"value={measured_val}, UCL={characteristic.upper_control_limit}, "
                            f"LCL={characteristic.lower_control_limit}"
                        )
            else:
                # For attribute characteristics, mark as conforming by default
                measurement.is_conforming = True

            # Track counts
            if measurement.is_conforming:
                conforming_count += 1
            else:
                non_conforming_count += 1

            db.add(measurement)
            measurement_records.append((measurement, characteristic))

        db.flush()  # Get IDs

        # Determine overall status
        inspection_status = "PASS" if non_conforming_count == 0 else "FAIL"

        db.commit()

        logger.info(
            f"Inspection logged: plan_id={plan.id}, status={inspection_status}, "
            f"measurements={len(measurement_records)}, conforming={conforming_count}, "
            f"non_conforming={non_conforming_count}"
        )

        # Build response
        measurement_responses = []
        for measurement, characteristic in measurement_records:
            db.refresh(measurement)
            measurement_responses.append(
                InspectionLogMeasurementResponse(
                    id=measurement.id,
                    characteristic_id=characteristic.id,
                    characteristic_name=characteristic.characteristic_name,
                    measured_value=measurement.measured_value,
                    measured_text=measurement.measured_text,
                    is_conforming=measurement.is_conforming,
                    deviation=measurement.deviation,
                    is_out_of_control=measurement.is_out_of_control,
                    sample_number=measurement.sample_number,
                    notes=measurement.notes
                )
            )

        return InspectionLogResponse(
            log_id=measurement_records[0][0].id if measurement_records else 0,
            inspection_plan_id=plan.id,
            plan_name=plan.plan_name,
            inspected_by_user_id=log_data.inspected_by_user_id,
            work_order_id=log_data.work_order_id,
            material_id=log_data.material_id,
            lot_number=log_data.lot_number,
            serial_number=log_data.serial_number,
            inspection_status=inspection_status,
            total_measurements=len(measurement_records),
            conforming_measurements=conforming_count,
            non_conforming_measurements=non_conforming_count,
            out_of_control_measurements=out_of_control_count,
            inspection_timestamp=datetime.now(timezone.utc),
            measurements=measurement_responses,
            notes=log_data.notes
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging inspection results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log inspection results: {str(e)}"
        )


# Helper function to build nested response
def _build_nested_plan_response(plan, db: Session) -> NestedInspectionPlanResponse:
    """
    Build a nested inspection plan response with all points and characteristics.

    Args:
        plan: InspectionPlan model instance
        db: Database session

    Returns:
        NestedInspectionPlanResponse with all nested data
    """
    points_response = []

    for point in plan.inspection_points:
        if not point.is_active:
            continue

        characteristics_response = [
            NestedCharacteristicResponse(
                id=char.id,
                characteristic_code=char.characteristic_code,
                characteristic_name=char.characteristic_name,
                description=char.description,
                characteristic_type=char.characteristic_type,
                data_type=char.data_type,
                unit_of_measure=char.unit_of_measure,
                target_value=char.target_value,
                lower_spec_limit=char.lower_spec_limit,
                upper_spec_limit=char.upper_spec_limit,
                lower_control_limit=char.lower_control_limit,
                upper_control_limit=char.upper_control_limit,
                track_spc=char.track_spc,
                control_chart_type=char.control_chart_type,
                subgroup_size=char.subgroup_size,
                allowed_values=char.allowed_values,
                tolerance_type=char.tolerance_type,
                tolerance=char.tolerance,
                is_active=char.is_active,
                sequence=char.sequence
            )
            for char in point.characteristics
            if char.is_active
        ]

        points_response.append(
            NestedPointResponse(
                id=point.id,
                point_code=point.point_code,
                point_name=point.point_name,
                description=point.description,
                inspection_method=point.inspection_method,
                inspection_equipment=point.inspection_equipment,
                sequence=point.sequence,
                is_mandatory=point.is_mandatory,
                is_critical=point.is_critical,
                inspection_instructions=point.inspection_instructions,
                acceptance_criteria=point.acceptance_criteria,
                is_active=point.is_active,
                characteristics=characteristics_response
            )
        )

    return NestedInspectionPlanResponse(
        id=plan.id,
        organization_id=plan.organization_id,
        plant_id=plan.plant_id,
        plan_code=plan.plan_code,
        plan_name=plan.plan_name,
        description=plan.description,
        plan_type=plan.plan_type,
        applies_to=plan.applies_to,
        material_id=plan.material_id,
        work_center_id=plan.work_center_id,
        frequency=plan.frequency,
        frequency_value=plan.frequency_value,
        sample_size=plan.sample_size,
        spc_enabled=plan.spc_enabled,
        control_limits_config=plan.control_limits_config,
        approved_by=plan.approved_by,
        approved_date=plan.approved_date,
        effective_date=plan.effective_date,
        expiry_date=plan.expiry_date,
        instructions=plan.instructions,
        acceptance_criteria=plan.acceptance_criteria,
        is_active=plan.is_active,
        revision=plan.revision,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        created_by=plan.created_by,
        inspection_points=points_response
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


# ==================== SPC Chart Endpoint ====================

@router.get("/spc-charts", response_model=SPCChartResponse)
def get_spc_chart_data(
    characteristic_id: int = Query(..., gt=0, description="Characteristic ID to analyze"),
    start_date: datetime = Query(..., description="Start date for analysis period"),
    end_date: datetime = Query(..., description="End date for analysis period"),
    control_limit_sigma: float = Query(3.0, ge=1.0, le=6.0, description="Number of standard deviations for control limits"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get SPC (Statistical Process Control) chart data for a characteristic.

    This endpoint performs comprehensive SPC analysis including:
    - Process capability indices (Cp, Cpk)
    - Control limits (UCL, LCL)
    - Statistical measures (mean, std dev)
    - Out-of-control and out-of-spec detection

    **Calculations:**
    - Cp = (USL - LSL) / (6 × σ)
    - Cpk = min[(USL - μ) / (3 × σ), (μ - LSL) / (3 × σ)]
    - UCL = μ + (control_limit_sigma × σ)
    - LCL = μ - (control_limit_sigma × σ)

    **Capability Assessment:**
    - Cpk >= 1.33: EXCELLENT
    - Cpk >= 1.00: CAPABLE
    - Cpk >= 0.67: MARGINAL
    - Cpk < 0.67: INCAPABLE

    Args:
        characteristic_id: ID of the inspection characteristic to analyze
        start_date: Start of time range for analysis
        end_date: End of time range for analysis
        control_limit_sigma: Number of standard deviations for control limits (default: 3.0)
        db: Database session
        current_user: Authenticated user

    Returns:
        SPCChartResponse with comprehensive SPC data

    Raises:
        HTTPException: If characteristic not found or insufficient data
    """
    try:
        organization_id = current_user.get("organization_id")

        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization context required"
            )

        logger.info(
            f"SPC chart request: char_id={characteristic_id}, "
            f"start={start_date}, end={end_date}, sigma={control_limit_sigma}"
        )

        # Get the characteristic
        from app.models.quality_enhancement import InspectionCharacteristic, InspectionMeasurement

        characteristic = db.query(InspectionCharacteristic).filter(
            InspectionCharacteristic.id == characteristic_id,
            InspectionCharacteristic.organization_id == organization_id
        ).first()

        if not characteristic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Characteristic with id {characteristic_id} not found"
            )

        # Only variable characteristics support SPC analysis
        if characteristic.characteristic_type != 'VARIABLE':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SPC analysis only available for VARIABLE characteristics. "
                       f"Characteristic {characteristic.characteristic_name} is {characteristic.characteristic_type}"
            )

        # Query measurements for the time period (optimized for TimescaleDB)
        measurements = db.query(InspectionMeasurement).filter(
            InspectionMeasurement.characteristic_id == characteristic_id,
            InspectionMeasurement.organization_id == organization_id,
            InspectionMeasurement.measurement_timestamp >= start_date,
            InspectionMeasurement.measurement_timestamp <= end_date,
            InspectionMeasurement.measured_value.isnot(None)
        ).order_by(InspectionMeasurement.measurement_timestamp.asc()).all()

        sample_size = len(measurements)

        logger.info(f"Retrieved {sample_size} measurements for SPC analysis")

        # Edge case: insufficient data
        if sample_size < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient data for SPC analysis. Found {sample_size} measurements, need at least 2."
            )

        # Extract measurement values
        values = [float(m.measured_value) for m in measurements]

        # Calculate statistical measures
        mean_value = statistics.mean(values)

        # Use sample standard deviation (n-1) for process capability
        if sample_size >= 2:
            std_dev_value = statistics.stdev(values)
        else:
            std_dev_value = 0.0

        logger.info(f"Statistics: mean={mean_value:.6f}, std_dev={std_dev_value:.6f}, n={sample_size}")

        # Calculate control limits
        ucl = mean_value + (control_limit_sigma * std_dev_value)
        lcl = mean_value - (control_limit_sigma * std_dev_value)

        # Get spec limits from characteristic
        usl = float(characteristic.upper_spec_limit) if characteristic.upper_spec_limit else None
        lsl = float(characteristic.lower_spec_limit) if characteristic.lower_spec_limit else None
        target = float(characteristic.target_value) if characteristic.target_value else None

        # Calculate Cp and Cpk
        cp = None
        cpk = None
        capability_assessment = "UNKNOWN"

        if usl is not None and lsl is not None and std_dev_value > 0:
            # Cp = (USL - LSL) / (6 × σ)
            cp = (usl - lsl) / (6 * std_dev_value)

            # Cpk = min[(USL - μ) / (3 × σ), (μ - LSL) / (3 × σ)]
            cpu = (usl - mean_value) / (3 * std_dev_value)
            cpl = (mean_value - lsl) / (3 * std_dev_value)
            cpk = min(cpu, cpl)

            # Capability assessment based on Cpk
            if cpk >= 1.33:
                capability_assessment = "EXCELLENT"
            elif cpk >= 1.00:
                capability_assessment = "CAPABLE"
            elif cpk >= 0.67:
                capability_assessment = "MARGINAL"
            else:
                capability_assessment = "INCAPABLE"

            logger.info(
                f"Process capability: Cp={cp:.3f}, Cpk={cpk:.3f}, "
                f"assessment={capability_assessment}"
            )
        elif std_dev_value == 0:
            capability_assessment = "NO_VARIATION"
            logger.warning("Standard deviation is zero - no process variation detected")
        elif usl is None or lsl is None:
            capability_assessment = "SPEC_LIMITS_MISSING"
            logger.warning(f"Spec limits missing: USL={usl}, LSL={lsl}")

        # Analyze each data point for out-of-control and out-of-spec
        data_points = []
        out_of_control_count = 0
        out_of_spec_count = 0

        for measurement in measurements:
            value = float(measurement.measured_value)

            # Check if out of control (beyond control limits)
            is_out_of_control = False
            if value > ucl or value < lcl:
                is_out_of_control = True
                out_of_control_count += 1

            # Check if out of spec (beyond specification limits)
            is_out_of_spec = False
            if usl is not None and value > usl:
                is_out_of_spec = True
                out_of_spec_count += 1
            elif lsl is not None and value < lsl:
                is_out_of_spec = True
                out_of_spec_count += 1

            data_points.append(
                SPCDataPoint(
                    timestamp=measurement.measurement_timestamp,
                    value=Decimal(str(value)),
                    is_out_of_control=is_out_of_control,
                    is_out_of_spec=is_out_of_spec
                )
            )

        logger.info(
            f"SPC analysis complete: out_of_control={out_of_control_count}, "
            f"out_of_spec={out_of_spec_count}"
        )

        # Build response
        return SPCChartResponse(
            characteristic_id=characteristic.id,
            characteristic_name=characteristic.characteristic_name,
            period_start=start_date,
            period_end=end_date,
            sample_size=sample_size,
            mean=Decimal(str(mean_value)),
            std_dev=Decimal(str(std_dev_value)),
            target_value=Decimal(str(target)) if target is not None else None,
            lower_spec_limit=Decimal(str(lsl)) if lsl is not None else None,
            upper_spec_limit=Decimal(str(usl)) if usl is not None else None,
            lower_control_limit=Decimal(str(lcl)),
            upper_control_limit=Decimal(str(ucl)),
            cp=Decimal(str(cp)) if cp is not None else None,
            cpk=Decimal(str(cpk)) if cpk is not None else None,
            capability_assessment=capability_assessment,
            out_of_control_count=out_of_control_count,
            out_of_spec_count=out_of_spec_count,
            data_points=data_points
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SPC chart: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SPC chart: {str(e)}"
        )
