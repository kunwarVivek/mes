"""
Lane and Lane Assignment API endpoints
Handles production lane scheduling and capacity management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.application.dtos.lane_dto import (
    LaneCreateRequest,
    LaneUpdateRequest,
    LaneResponse,
    LaneListResponse,
    LaneAssignmentCreateRequest,
    LaneAssignmentUpdateRequest,
    LaneAssignmentResponse,
    LaneAssignmentListResponse,
    LaneCapacityResponse
)
from app.infrastructure.repositories.lane_repository import LaneRepository
from app.domain.entities.lane import LaneAssignmentStatus


router = APIRouter(prefix="/lanes", tags=["lanes"])


# ========================
# Lane Endpoints
# ========================

@router.post("/", response_model=LaneResponse, status_code=201)
def create_lane(dto: LaneCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new production lane

    Args:
        dto: Lane creation request
        db: Database session

    Returns:
        Created lane

    Raises:
        409: If lane_code already exists in plant
    """
    repo = LaneRepository(db)
    try:
        lane = repo.create_lane(dto)
        return lane
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=LaneListResponse)
def list_lanes(
    plant_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List lanes with optional filters and pagination

    Args:
        plant_id: Filter by plant ID
        is_active: Filter by active status
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        db: Database session

    Returns:
        Paginated list of lanes
    """
    repo = LaneRepository(db)
    return repo.list_lanes(
        plant_id=plant_id,
        is_active=is_active,
        page=page,
        page_size=page_size
    )


@router.get("/{lane_id}", response_model=LaneResponse)
def get_lane(lane_id: int, db: Session = Depends(get_db)):
    """
    Get a single lane by ID

    Args:
        lane_id: Lane ID
        db: Database session

    Returns:
        Lane details

    Raises:
        404: If lane not found
    """
    repo = LaneRepository(db)
    lane = repo.get_lane_by_id(lane_id)
    if not lane:
        raise HTTPException(status_code=404, detail=f"Lane {lane_id} not found")
    return lane


@router.put("/{lane_id}", response_model=LaneResponse)
def update_lane(
    lane_id: int,
    dto: LaneUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a lane

    Args:
        lane_id: Lane ID
        dto: Update request
        db: Database session

    Returns:
        Updated lane

    Raises:
        404: If lane not found
    """
    repo = LaneRepository(db)
    lane = repo.update_lane(lane_id, dto)
    if not lane:
        raise HTTPException(status_code=404, detail=f"Lane {lane_id} not found")
    return lane


@router.delete("/{lane_id}", status_code=204)
def delete_lane(lane_id: int, db: Session = Depends(get_db)):
    """
    Soft delete a lane (set is_active = False)

    Args:
        lane_id: Lane ID
        db: Database session

    Raises:
        404: If lane not found
    """
    repo = LaneRepository(db)
    success = repo.delete_lane(lane_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Lane {lane_id} not found")


@router.get("/{lane_id}/capacity", response_model=LaneCapacityResponse)
def get_lane_capacity(
    lane_id: int,
    date: date = Query(..., description="Date to check capacity for"),
    db: Session = Depends(get_db)
):
    """
    Get capacity utilization for a lane on a specific date

    Args:
        lane_id: Lane ID
        date: Target date
        db: Database session

    Returns:
        Capacity utilization details

    Raises:
        404: If lane not found
    """
    repo = LaneRepository(db)
    capacity = repo.get_lane_capacity(lane_id, date)
    if not capacity:
        raise HTTPException(status_code=404, detail=f"Lane {lane_id} not found")
    return capacity


# ========================
# Lane Assignment Endpoints
# ========================

@router.post("/assignments", response_model=LaneAssignmentResponse, status_code=201)
def create_assignment(
    dto: LaneAssignmentCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new lane assignment

    Args:
        dto: Assignment creation request
        db: Database session

    Returns:
        Created assignment

    Raises:
        400: If validation fails (lane not found, capacity exceeded, etc.)
    """
    repo = LaneRepository(db)
    try:
        assignment = repo.create_assignment(dto)
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/assignments", response_model=LaneAssignmentListResponse)
def list_assignments(
    lane_id: Optional[int] = None,
    plant_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[LaneAssignmentStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List lane assignments with optional filters and pagination

    Args:
        lane_id: Filter by lane ID
        plant_id: Filter by plant ID
        start_date: Filter assignments ending on or after this date
        end_date: Filter assignments starting on or before this date
        status: Filter by status
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        db: Database session

    Returns:
        Paginated list of assignments
    """
    repo = LaneRepository(db)
    return repo.list_assignments(
        lane_id=lane_id,
        plant_id=plant_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        page=page,
        page_size=page_size
    )


@router.get("/assignments/{assignment_id}", response_model=LaneAssignmentResponse)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """
    Get a single assignment by ID

    Args:
        assignment_id: Assignment ID
        db: Database session

    Returns:
        Assignment details

    Raises:
        404: If assignment not found
    """
    repo = LaneRepository(db)
    assignment = repo.get_assignment_by_id(assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail=f"Assignment {assignment_id} not found"
        )
    return assignment


@router.put("/assignments/{assignment_id}", response_model=LaneAssignmentResponse)
def update_assignment(
    assignment_id: int,
    dto: LaneAssignmentUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a lane assignment

    Args:
        assignment_id: Assignment ID
        dto: Update request
        db: Database session

    Returns:
        Updated assignment

    Raises:
        404: If assignment not found
    """
    repo = LaneRepository(db)
    assignment = repo.update_assignment(assignment_id, dto)
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail=f"Assignment {assignment_id} not found"
        )
    return assignment


@router.delete("/assignments/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """
    Delete a lane assignment

    Args:
        assignment_id: Assignment ID
        db: Database session

    Raises:
        404: If assignment not found
    """
    repo = LaneRepository(db)
    success = repo.delete_assignment(assignment_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Assignment {assignment_id} not found"
        )
