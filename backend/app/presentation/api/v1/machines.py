"""
Machine API endpoints for Equipment & Machines module.

Endpoints:
- POST /machines: Create machine
- GET /machines: List machines with pagination
- GET /machines/{id}: Get machine by ID
- PATCH /machines/{id}/status: Update machine status
- GET /machines/{id}/oee: Calculate OEE metrics
- GET /machines/{id}/utilization: Get machine utilization metrics
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.infrastructure.repositories.machine_repository import MachineRepository
from app.application.dtos.machine_dto import (
    MachineCreateDTO,
    MachineResponseDTO,
    MachineListResponseDTO,
    MachineStatusUpdateDTO,
    MachineStatusUpdateResponseDTO,
    MachineStatusHistoryResponseDTO,
    OEEMetricsDTO,
    OEECalculationRequestDTO,
    MachineUtilizationDTO
)
from app.domain.entities.machine import OEECalculator

router = APIRouter()


@router.post(
    "",
    response_model=MachineResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create new machine",
    description="Create a new machine with validation. Machine code must be unique within organization."
)
def create_machine(
    machine: MachineCreateDTO,
    db: Session = Depends(get_db)
):
    """Create a new machine"""
    repository = MachineRepository(db)

    try:
        db_machine = repository.create(machine.model_dump())
        return MachineResponseDTO.model_validate(db_machine)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=MachineListResponseDTO,
    summary="List machines",
    description="Get paginated list of machines with optional filtering"
)
def list_machines(
    organization_id: int = Query(..., gt=0, description="Organization ID"),
    plant_id: Optional[int] = Query(None, gt=0, description="Plant ID filter"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    work_center_id: Optional[int] = Query(None, gt=0, description="Filter by work center"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List machines with pagination and filtering"""
    repository = MachineRepository(db)

    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if work_center_id:
        filters["work_center_id"] = work_center_id
    if is_active is not None:
        filters["is_active"] = is_active

    result = repository.list_by_organization(
        org_id=organization_id,
        plant_id=plant_id,
        filters=filters,
        page=page,
        page_size=page_size
    )

    return MachineListResponseDTO(
        items=[MachineResponseDTO.model_validate(m) for m in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"]
    )


@router.get(
    "/{machine_id}",
    response_model=MachineResponseDTO,
    summary="Get machine by ID",
    description="Retrieve specific machine by ID"
)
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db)
):
    """Get machine by ID"""
    repository = MachineRepository(db)
    db_machine = repository.get_by_id(machine_id)

    if not db_machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with id {machine_id} not found"
        )

    return MachineResponseDTO.model_validate(db_machine)


@router.patch(
    "/{machine_id}/status",
    response_model=MachineStatusUpdateResponseDTO,
    summary="Update machine status",
    description="Change machine status and create status history record"
)
def update_machine_status(
    machine_id: int,
    status_update: MachineStatusUpdateDTO,
    db: Session = Depends(get_db)
):
    """Update machine status"""
    repository = MachineRepository(db)

    try:
        db_machine, status_history = repository.change_status(
            machine_id=machine_id,
            new_status=status_update.status,
            notes=status_update.notes
        )

        # Calculate duration for history response
        duration = None
        if status_history.ended_at:
            duration = (status_history.ended_at - status_history.started_at).total_seconds() / 60.0

        history_dto = MachineStatusHistoryResponseDTO(
            id=status_history.id,
            machine_id=status_history.machine_id,
            status=status_history.status,
            started_at=status_history.started_at,
            ended_at=status_history.ended_at,
            notes=status_history.notes,
            duration_minutes=duration
        )

        return MachineStatusUpdateResponseDTO(
            machine=MachineResponseDTO.model_validate(db_machine),
            status_history=history_dto
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{machine_id}/status-history",
    response_model=list[MachineStatusHistoryResponseDTO],
    summary="Get machine status history",
    description="Retrieve status history for a machine within optional time range"
)
def get_machine_status_history(
    machine_id: int,
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records"),
    db: Session = Depends(get_db)
):
    """Get machine status history"""
    repository = MachineRepository(db)

    # Verify machine exists
    db_machine = repository.get_by_id(machine_id)
    if not db_machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with id {machine_id} not found"
        )

    history_records = repository.get_status_history(
        machine_id=machine_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

    results = []
    for record in history_records:
        duration = None
        if record.ended_at:
            duration = (record.ended_at - record.started_at).total_seconds() / 60.0

        results.append(MachineStatusHistoryResponseDTO(
            id=record.id,
            machine_id=record.machine_id,
            status=record.status,
            started_at=record.started_at,
            ended_at=record.ended_at,
            notes=record.notes,
            duration_minutes=duration
        ))

    return results


@router.get(
    "/{machine_id}/oee",
    response_model=OEEMetricsDTO,
    summary="Calculate OEE metrics",
    description="Calculate Overall Equipment Effectiveness (OEE) for a machine over a time period"
)
def calculate_machine_oee(
    machine_id: int,
    start_date: datetime = Query(..., description="Start of time period"),
    end_date: datetime = Query(..., description="End of time period"),
    ideal_cycle_time: float = Query(..., gt=0, description="Ideal cycle time per piece (minutes)"),
    total_pieces: int = Query(..., ge=0, description="Total pieces produced"),
    defect_pieces: int = Query(0, ge=0, description="Number of defective pieces"),
    db: Session = Depends(get_db)
):
    """
    Calculate OEE metrics for a machine.

    OEE = Availability × Performance × Quality

    - Availability: Based on downtime from status history
    - Performance: Based on actual vs ideal production rate
    - Quality: Based on good pieces vs total pieces
    """
    repository = MachineRepository(db)

    # Verify machine exists
    db_machine = repository.get_by_id(machine_id)
    if not db_machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with id {machine_id} not found"
        )

    # Validate date range
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Validate defects
    if defect_pieces > total_pieces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="defect_pieces cannot exceed total_pieces"
        )

    # Calculate total time and downtime
    total_time_minutes = (end_date - start_date).total_seconds() / 60.0
    downtime_minutes = repository.calculate_downtime(
        machine_id=machine_id,
        start_date=start_date,
        end_date=end_date
    )

    # Calculate OEE using domain service
    try:
        oee_metrics = OEECalculator.calculate_oee(
            total_time_minutes=total_time_minutes,
            downtime_minutes=downtime_minutes,
            ideal_cycle_time=ideal_cycle_time,
            total_pieces=total_pieces,
            defect_pieces=defect_pieces
        )

        return OEEMetricsDTO(
            availability=oee_metrics.availability,
            performance=oee_metrics.performance,
            quality=oee_metrics.quality,
            oee_score=oee_metrics.oee_score
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{machine_id}/utilization",
    response_model=MachineUtilizationDTO,
    summary="Get machine utilization metrics",
    description="Calculate machine utilization and OEE availability for a time period"
)
def get_machine_utilization(
    machine_id: int,
    start_date: datetime = Query(..., description="Start of time period"),
    end_date: datetime = Query(..., description="End of time period"),
    db: Session = Depends(get_db)
):
    """
    Get machine utilization metrics for a time period.

    Calculates:
    - Utilization percentage: (Running time / Total time) × 100
    - Total running hours: Time machine spent in RUNNING status
    - Total downtime hours: Time machine spent in DOWN or MAINTENANCE status
    - OEE Availability: (Planned time - Unplanned downtime) / Planned time × 100

    Returns comprehensive utilization metrics including OEE availability.
    OEE performance and quality are null as they require additional production data.
    """
    repository = MachineRepository(db)

    # Verify machine exists
    db_machine = repository.get_by_id(machine_id)
    if not db_machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with id {machine_id} not found"
        )

    # Validate date range
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Calculate utilization metrics
    utilization_metrics = repository.calculate_utilization(
        machine_id=machine_id,
        start_date=start_date,
        end_date=end_date
    )

    # Build response DTO
    return MachineUtilizationDTO(
        machine_id=db_machine.id,
        machine_code=db_machine.machine_code,
        period_start=start_date,
        period_end=end_date,
        utilization_percent=round(utilization_metrics["utilization_percent"], 2),
        total_available_hours=round(utilization_metrics["total_available_hours"], 2),
        total_running_hours=round(utilization_metrics["total_running_hours"], 2),
        total_downtime_hours=round(utilization_metrics["total_downtime_hours"], 2),
        oee_availability=round(utilization_metrics["oee_availability"], 2),
        oee_performance=None,  # Requires ideal_cycle_time and production data
        oee_quality=None,  # Requires good_units/total_units from quality system
        oee_overall=None,  # Product of availability × performance × quality
        capacity_units_per_hour=db_machine.capacity_units_per_hour
    )
