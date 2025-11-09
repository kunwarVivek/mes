"""
Shift Management API Router - Presentation layer endpoints.

Provides RESTful API for Shift and Shift Handover management with:
- JWT authentication (all endpoints)
- RLS context from authenticated user
- Pagination and filtering
- Request/response validation via Pydantic
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.infrastructure.repositories.shift_repository import (
    ShiftRepository,
    ShiftHandoverRepository,
    ShiftPerformanceRepository
)
from app.application.dtos.shift_dto import (
    ShiftCreateRequest,
    ShiftUpdateRequest,
    ShiftResponse,
    ShiftListResponse,
    ShiftHandoverCreateRequest,
    ShiftHandoverAcknowledgeRequest,
    ShiftHandoverResponse,
    ShiftHandoverListResponse,
    ShiftPerformanceResponse,
    ShiftPerformanceListResponse,
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    ConflictErrorResponse,
)
from app.models.shift import Shift, ShiftHandover, ShiftPerformance
from app.infrastructure.security.dependencies import get_user_context
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency injection
def get_shift_repository(db: Session = Depends(get_db)) -> ShiftRepository:
    """Dependency injection for ShiftRepository"""
    return ShiftRepository(db)


def get_shift_handover_repository(db: Session = Depends(get_db)) -> ShiftHandoverRepository:
    """Dependency injection for ShiftHandoverRepository"""
    return ShiftHandoverRepository(db)


def get_shift_performance_repository(db: Session = Depends(get_db)) -> ShiftPerformanceRepository:
    """Dependency injection for ShiftPerformanceRepository"""
    return ShiftPerformanceRepository(db)


# Shift endpoints
@router.post(
    "/",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new shift",
    description="Create a new shift pattern with start/end times and production target.",
    responses={
        201: {"description": "Shift created successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ConflictErrorResponse, "description": "Shift code already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Shifts"],
)
def create_shift(
    shift_data: ShiftCreateRequest,
    repository: ShiftRepository = Depends(get_shift_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Create a new shift pattern.

    - **shift_name**: Descriptive name for the shift
    - **shift_code**: Unique code (will be uppercased)
    - **start_time**: Shift start time (HH:MM:SS)
    - **end_time**: Shift end time (HH:MM:SS, can be next day for overnight shifts)
    - **production_target**: Target production quantity for the shift
    - **is_active**: Whether shift is currently active (default: true)
    """
    try:
        logger.info(f"Creating shift: {shift_data.shift_code} (user: {user_context['id']})")

        org_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        shift_dict = {
            "organization_id": org_id,
            "plant_id": plant_id,
            "shift_name": shift_data.shift_name,
            "shift_code": shift_data.shift_code,
            "start_time": shift_data.start_time,
            "end_time": shift_data.end_time,
            "production_target": shift_data.production_target,
            "is_active": shift_data.is_active,
        }

        db_shift = repository.create(shift_dict)

        logger.info(f"Shift created successfully: {db_shift.shift_code}")
        return ShiftResponse.model_validate(db_shift)

    except ValueError as e:
        if "already exists" in str(e):
            logger.warning(f"Duplicate shift code: {shift_data.shift_code}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create shift: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create shift")


@router.get(
    "/{shift_id}",
    response_model=ShiftResponse,
    summary="Get shift by ID",
    description="Retrieve a shift by its ID. RLS filtering is automatic.",
    responses={
        200: {"description": "Shift found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shift not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Shifts"],
)
def get_shift(
    shift_id: int,
    repository: ShiftRepository = Depends(get_shift_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Get shift by ID.

    RLS filtering is automatically applied from the authenticated user's organization/plant context.
    """
    try:
        logger.info(f"Fetching shift with ID: {shift_id}")

        db_shift = repository.get_by_id(shift_id)

        if not db_shift:
            logger.warning(f"Shift not found: {shift_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")

        return ShiftResponse.model_validate(db_shift)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch shift: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch shift")


@router.get(
    "/",
    response_model=ShiftListResponse,
    summary="List shifts with pagination",
    description="List shifts with pagination and optional filters (active status, shift code).",
    responses={
        200: {"description": "Shift list retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Shifts"],
)
def list_shifts(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    shift_code: Optional[str] = Query(None, description="Filter by shift code"),
    repository: ShiftRepository = Depends(get_shift_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    List shifts with pagination and filters.

    Automatically filtered by authenticated user's organization/plant (RLS).
    """
    try:
        logger.info(f"Listing shifts: page={page}, page_size={page_size}")

        org_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        if shift_code is not None:
            filters["shift_code"] = shift_code

        result = repository.list_by_organization(
            org_id=org_id,
            plant_id=plant_id,
            filters=filters if filters else None,
            page=page,
            page_size=page_size,
        )

        items = [ShiftResponse.model_validate(shift) for shift in result["items"]]

        return ShiftListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list shifts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list shifts")


@router.put(
    "/{shift_id}",
    response_model=ShiftResponse,
    summary="Update shift",
    description="Update an existing shift. Supports partial updates.",
    responses={
        200: {"description": "Shift updated successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shift not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Shifts"],
)
def update_shift(
    shift_id: int,
    update_data: ShiftUpdateRequest,
    repository: ShiftRepository = Depends(get_shift_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Update shift by ID.

    Only provided fields will be updated (partial updates supported).
    Shift code, organization_id, and plant_id cannot be updated.
    """
    try:
        logger.info(f"Updating shift: {shift_id}")

        update_dict = update_data.model_dump(exclude_unset=True)
        db_shift = repository.update(shift_id, update_dict)

        logger.info(f"Shift updated successfully: {shift_id}")
        return ShiftResponse.model_validate(db_shift)

    except ValueError as e:
        if "not found" in str(e):
            logger.warning(f"Shift not found: {shift_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to update shift: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update shift")


# Shift Handover endpoints
@router.post(
    "/handovers",
    response_model=ShiftHandoverResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create shift handover",
    description="Create a new shift handover with production summary and status.",
    responses={
        201: {"description": "Shift handover created successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shift not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Shift Handovers"],
)
def create_shift_handover(
    handover_data: ShiftHandoverCreateRequest,
    repository: ShiftHandoverRepository = Depends(get_shift_handover_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Create a new shift handover.

    - **from_shift_id**: ID of shift handing over
    - **to_shift_id**: ID of shift receiving handover
    - **handover_date**: Date and time of handover
    - **wip_quantity**: Work-in-progress quantity
    - **production_summary**: Summary of production activities
    - **quality_issues**: Optional quality issues encountered
    - **machine_status**: Optional machine status summary
    - **material_status**: Optional material availability status
    - **safety_incidents**: Optional safety incidents
    """
    try:
        logger.info(f"Creating shift handover from {handover_data.from_shift_id} to {handover_data.to_shift_id}")

        org_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")
        user_id = user_context.get("id")

        handover_dict = {
            "organization_id": org_id,
            "plant_id": plant_id,
            "from_shift_id": handover_data.from_shift_id,
            "to_shift_id": handover_data.to_shift_id,
            "handover_date": handover_data.handover_date,
            "wip_quantity": handover_data.wip_quantity,
            "production_summary": handover_data.production_summary,
            "quality_issues": handover_data.quality_issues,
            "machine_status": handover_data.machine_status,
            "material_status": handover_data.material_status,
            "safety_incidents": handover_data.safety_incidents,
            "handover_by_user_id": user_id,
        }

        db_handover = repository.create(handover_dict)

        logger.info(f"Shift handover created successfully: {db_handover.id}")
        return ShiftHandoverResponse.model_validate(db_handover)

    except ValueError as e:
        if "not found" in str(e):
            logger.warning(f"Shift not found: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create shift handover: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create shift handover")


@router.post(
    "/handovers/{handover_id}/acknowledge",
    response_model=ShiftHandoverResponse,
    summary="Acknowledge shift handover",
    description="Acknowledge receipt of a shift handover.",
    responses={
        200: {"description": "Shift handover acknowledged successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Shift handover not found"},
        409: {"model": ConflictErrorResponse, "description": "Already acknowledged"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Shift Handovers"],
)
def acknowledge_shift_handover(
    handover_id: int,
    repository: ShiftHandoverRepository = Depends(get_shift_handover_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Acknowledge shift handover.

    Records the receiving shift supervisor's acknowledgment.
    """
    try:
        logger.info(f"Acknowledging shift handover: {handover_id}")

        user_id = user_context.get("id")
        db_handover = repository.acknowledge(handover_id, user_id)

        logger.info(f"Shift handover acknowledged successfully: {handover_id}")
        return ShiftHandoverResponse.model_validate(db_handover)

    except ValueError as e:
        if "not found" in str(e):
            logger.warning(f"Shift handover not found: {handover_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "already acknowledged" in str(e):
            logger.warning(f"Shift handover already acknowledged: {handover_id}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to acknowledge shift handover: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to acknowledge shift handover")


@router.get(
    "/handovers",
    response_model=ShiftHandoverListResponse,
    summary="List shift handovers with pagination",
    description="List shift handovers with pagination and optional filters.",
    responses={
        200: {"description": "Shift handover list retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Shift Handovers"],
)
def list_shift_handovers(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    from_shift_id: Optional[int] = Query(None, description="Filter by from shift ID"),
    to_shift_id: Optional[int] = Query(None, description="Filter by to shift ID"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    repository: ShiftHandoverRepository = Depends(get_shift_handover_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    List shift handovers with pagination and filters.

    Automatically filtered by authenticated user's organization/plant (RLS).
    """
    try:
        logger.info(f"Listing shift handovers: page={page}, page_size={page_size}")

        org_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        filters = {}
        if from_shift_id is not None:
            filters["from_shift_id"] = from_shift_id
        if to_shift_id is not None:
            filters["to_shift_id"] = to_shift_id
        if acknowledged is not None:
            filters["acknowledged"] = acknowledged

        result = repository.list_by_organization(
            org_id=org_id,
            plant_id=plant_id,
            filters=filters if filters else None,
            page=page,
            page_size=page_size,
        )

        items = [ShiftHandoverResponse.model_validate(handover) for handover in result["items"]]

        return ShiftHandoverListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list shift handovers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list shift handovers")


# Shift Performance endpoints
@router.get(
    "/performance",
    response_model=ShiftPerformanceListResponse,
    summary="Get shift performance metrics",
    description="Get shift performance metrics with optional date range filtering.",
    responses={
        200: {"description": "Shift performance retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Shift Performance"],
)
def get_shift_performance(
    shift_id: int = Query(..., description="Shift ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    repository: ShiftPerformanceRepository = Depends(get_shift_performance_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Get shift performance metrics.

    Returns performance metrics including target attainment, OEE, and FPY.
    """
    try:
        logger.info(f"Fetching shift performance for shift {shift_id}")

        result = repository.list_by_shift(
            shift_id=shift_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

        items = [ShiftPerformanceResponse.model_validate(perf) for perf in result["items"]]

        return ShiftPerformanceListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to fetch shift performance: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch shift performance")
