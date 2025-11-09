"""
API endpoints for Maintenance Management module.
Handles PM schedules, PM work orders, downtime events, and MTBF/MTTR metrics.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_active_user
from app.application.dtos.maintenance_dto import (
    PMScheduleCreateDTO, PMScheduleUpdateDTO, PMScheduleResponseDTO,
    PMWorkOrderCreateDTO, PMWorkOrderUpdateDTO, PMWorkOrderResponseDTO,
    DowntimeEventCreateDTO, DowntimeEventUpdateDTO, DowntimeEventResponseDTO,
    MTBFMTTRMetricsDTO, MTBFMTTRQueryDTO
)
from app.domain.entities.maintenance import (
    PMScheduleDomain, PMWorkOrderDomain, DowntimeEventDomain,
    TriggerType, PMStatus, DowntimeCategory
)
from app.infrastructure.repositories.maintenance_repository import MaintenanceRepository

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


# PM Schedule Endpoints
@router.post("/pm-schedules", response_model=PMScheduleResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_pm_schedule(
    schedule_dto: PMScheduleCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new PM schedule"""
    repository = MaintenanceRepository(db)

    # Create domain entity (validates business rules)
    try:
        schedule_domain = PMScheduleDomain(
            id=None,
            organization_id=current_user["organization_id"],
            plant_id=current_user["plant_id"],
            schedule_code=schedule_dto.schedule_code,
            schedule_name=schedule_dto.schedule_name,
            machine_id=schedule_dto.machine_id,
            trigger_type=schedule_dto.trigger_type,
            frequency_days=schedule_dto.frequency_days,
            meter_threshold=schedule_dto.meter_threshold,
            is_active=schedule_dto.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Persist to database
    pm_schedule = repository.create_pm_schedule(
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        schedule_domain=schedule_domain
    )

    return pm_schedule


@router.get("/pm-schedules", response_model=List[PMScheduleResponseDTO])
async def get_pm_schedules(
    machine_id: Optional[int] = Query(None, description="Filter by machine ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all PM schedules with optional filters"""
    repository = MaintenanceRepository(db)

    schedules = repository.get_pm_schedules(
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        machine_id=machine_id,
        is_active=is_active
    )

    return schedules


@router.get("/pm-schedules/{schedule_id}", response_model=PMScheduleResponseDTO)
async def get_pm_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get PM schedule by ID"""
    repository = MaintenanceRepository(db)

    schedule = repository.get_pm_schedule_by_id(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"]
    )

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PM Schedule {schedule_id} not found"
        )

    return schedule


@router.patch("/pm-schedules/{schedule_id}", response_model=PMScheduleResponseDTO)
async def update_pm_schedule(
    schedule_id: int,
    schedule_dto: PMScheduleUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update PM schedule"""
    repository = MaintenanceRepository(db)

    updated_schedule = repository.update_pm_schedule(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        **schedule_dto.model_dump(exclude_unset=True)
    )

    if not updated_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PM Schedule {schedule_id} not found"
        )

    return updated_schedule


@router.delete("/pm-schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pm_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Delete PM schedule"""
    repository = MaintenanceRepository(db)

    deleted = repository.delete_pm_schedule(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"]
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PM Schedule {schedule_id} not found"
        )


# PM Work Order Endpoints
@router.post("/pm-work-orders", response_model=PMWorkOrderResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_pm_work_order(
    work_order_dto: PMWorkOrderCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new PM work order (typically auto-generated by pg_cron)"""
    repository = MaintenanceRepository(db)

    # Create domain entity (validates business rules)
    try:
        work_order_domain = PMWorkOrderDomain(
            id=None,
            organization_id=current_user["organization_id"],
            plant_id=current_user["plant_id"],
            pm_schedule_id=work_order_dto.pm_schedule_id,
            machine_id=work_order_dto.machine_id,
            pm_number=work_order_dto.pm_number,
            status=PMStatus.SCHEDULED,
            scheduled_date=work_order_dto.scheduled_date,
            due_date=work_order_dto.due_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Persist to database
    pm_work_order = repository.create_pm_work_order(
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        work_order_domain=work_order_domain
    )

    return pm_work_order


@router.get("/pm-work-orders", response_model=List[PMWorkOrderResponseDTO])
async def get_pm_work_orders(
    machine_id: Optional[int] = Query(None, description="Filter by machine ID"),
    status_filter: Optional[PMStatus] = Query(None, alias="status", description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by scheduled date start"),
    end_date: Optional[datetime] = Query(None, description="Filter by scheduled date end"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all PM work orders with optional filters"""
    repository = MaintenanceRepository(db)

    work_orders = repository.get_pm_work_orders(
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        machine_id=machine_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date
    )

    return work_orders


@router.get("/pm-work-orders/{work_order_id}", response_model=PMWorkOrderResponseDTO)
async def get_pm_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get PM work order by ID"""
    repository = MaintenanceRepository(db)

    work_order = repository.get_pm_work_order_by_id(
        work_order_id=work_order_id,
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"]
    )

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PM Work Order {work_order_id} not found"
        )

    return work_order


@router.patch("/pm-work-orders/{work_order_id}", response_model=PMWorkOrderResponseDTO)
async def update_pm_work_order(
    work_order_id: int,
    work_order_dto: PMWorkOrderUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update PM work order status or notes"""
    repository = MaintenanceRepository(db)

    updated_work_order = repository.update_pm_work_order(
        work_order_id=work_order_id,
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        **work_order_dto.model_dump(exclude_unset=True)
    )

    if not updated_work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PM Work Order {work_order_id} not found"
        )

    return updated_work_order


# Downtime Event Endpoints
@router.post("/downtime-events", response_model=DowntimeEventResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_downtime_event(
    event_dto: DowntimeEventCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new downtime event"""
    repository = MaintenanceRepository(db)

    # Create domain entity (validates business rules)
    try:
        event_domain = DowntimeEventDomain(
            id=None,
            organization_id=current_user["organization_id"],
            plant_id=current_user["plant_id"],
            machine_id=event_dto.machine_id,
            category=event_dto.category,
            reason=event_dto.reason,
            started_at=event_dto.started_at,
            ended_at=event_dto.ended_at,
            notes=event_dto.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Persist to database
    downtime_event = repository.create_downtime_event(
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        event_domain=event_domain
    )

    # Add duration to response
    response = DowntimeEventResponseDTO.model_validate(downtime_event)
    if downtime_event.ended_at:
        response.duration_minutes = (downtime_event.ended_at - downtime_event.started_at).total_seconds() / 60.0
    else:
        response.duration_minutes = None

    return response


@router.get("/downtime-events", response_model=List[DowntimeEventResponseDTO])
async def get_downtime_events(
    machine_id: Optional[int] = Query(None, description="Filter by machine ID"),
    category: Optional[DowntimeCategory] = Query(None, description="Filter by category"),
    start_date: Optional[datetime] = Query(None, description="Filter by event start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by event end date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all downtime events with optional filters"""
    repository = MaintenanceRepository(db)

    events = repository.get_downtime_events(
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        machine_id=machine_id,
        category=category,
        start_date=start_date,
        end_date=end_date
    )

    # Add duration to each response
    responses = []
    for event in events:
        response = DowntimeEventResponseDTO.model_validate(event)
        if event.ended_at:
            response.duration_minutes = (event.ended_at - event.started_at).total_seconds() / 60.0
        else:
            response.duration_minutes = None
        responses.append(response)

    return responses


@router.patch("/downtime-events/{event_id}", response_model=DowntimeEventResponseDTO)
async def update_downtime_event(
    event_id: int,
    event_dto: DowntimeEventUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update downtime event (typically to set end time)"""
    repository = MaintenanceRepository(db)

    updated_event = repository.update_downtime_event(
        event_id=event_id,
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        **event_dto.model_dump(exclude_unset=True)
    )

    if not updated_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Downtime Event {event_id} not found"
        )

    # Add duration to response
    response = DowntimeEventResponseDTO.model_validate(updated_event)
    if updated_event.ended_at:
        response.duration_minutes = (updated_event.ended_at - updated_event.started_at).total_seconds() / 60.0
    else:
        response.duration_minutes = None

    return response


# MTBF/MTTR Metrics Endpoint
@router.get("/metrics/mtbf-mttr", response_model=MTBFMTTRMetricsDTO)
async def get_mtbf_mttr_metrics(
    machine_id: int = Query(..., description="Machine ID for metrics calculation"),
    start_date: datetime = Query(..., description="Start date for metrics period"),
    end_date: datetime = Query(..., description="End date for metrics period"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Calculate MTBF/MTTR metrics for a machine within a date range"""
    repository = MaintenanceRepository(db)

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date"
        )

    # Calculate metrics
    try:
        metrics = repository.calculate_mtbf_mttr(
            organization_id=current_user["organization_id"],
            plant_id=current_user["plant_id"],
            machine_id=machine_id,
            start_date=start_date,
            end_date=end_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Calculate total operating and repair time for response
    total_time_in_period = (end_date - start_date).total_seconds() / 60.0

    # Get breakdown events for repair time
    breakdown_events = repository.get_downtime_events(
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        machine_id=machine_id,
        category=DowntimeCategory.BREAKDOWN,
        start_date=start_date,
        end_date=end_date
    )

    total_repair_time = sum(
        (event.ended_at - event.started_at).total_seconds() / 60.0
        for event in breakdown_events if event.ended_at
    )

    # Get all downtime for operating time calculation
    all_downtime_events = repository.get_downtime_events(
        organization_id=current_user["organization_id"],
        plant_id=current_user["plant_id"],
        machine_id=machine_id,
        start_date=start_date,
        end_date=end_date
    )

    total_downtime = sum(
        (event.ended_at - event.started_at).total_seconds() / 60.0
        for event in all_downtime_events if event.ended_at
    )

    total_operating_time = max(0.0, total_time_in_period - total_downtime)

    return MTBFMTTRMetricsDTO(
        machine_id=machine_id,
        time_period_start=start_date,
        time_period_end=end_date,
        total_operating_time=total_operating_time,
        total_repair_time=total_repair_time,
        number_of_failures=len([e for e in breakdown_events if e.ended_at]),
        mtbf=metrics.mtbf,
        mttr=metrics.mttr,
        availability=metrics.availability
    )
