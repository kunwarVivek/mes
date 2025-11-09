"""
Work Order API Router - Presentation layer endpoints for Work Order management.

Provides RESTful API for Work Order CRUD and state management with:
- JWT authentication (all endpoints)
- RLS context from authenticated user
- Pagination and filtering
- State transitions (PLANNED -> RELEASED -> IN_PROGRESS -> COMPLETED)
- Request/response validation via Pydantic

Phase 3 Component 5: Work Order API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.infrastructure.repositories.work_order_repository import WorkOrderRepository
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.application.dtos.work_order_dto import (
    WorkOrderCreateRequest,
    WorkOrderUpdateRequest,
    WorkOrderResponse,
    WorkOrderListResponse,
    WorkOrderOperationCreateRequest,
    WorkOrderMaterialCreateRequest,
    WorkOrderOperationResponse,
    WorkOrderMaterialResponse,
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    ConflictErrorResponse,
)
from app.models.work_order import WorkOrder, WorkOrderOperation, WorkOrderMaterial, OrderStatus
from app.models.material import Material
from app.infrastructure.security.dependencies import get_user_context


logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency to get WorkOrderRepository
def get_work_order_repository(db: Session = Depends(get_db)) -> WorkOrderRepository:
    """Dependency injection for WorkOrderRepository"""
    return WorkOrderRepository(db)


def get_material_repository(db: Session = Depends(get_db)) -> MaterialRepository:
    """Dependency injection for MaterialRepository"""
    return MaterialRepository(db, use_pg_search=False)


def map_work_order_to_response(work_order: WorkOrder) -> WorkOrderResponse:
    """Map WorkOrder entity to WorkOrderResponse DTO"""
    return WorkOrderResponse(
        id=work_order.id,
        organization_id=work_order.organization_id,
        plant_id=work_order.plant_id,
        work_order_number=work_order.work_order_number,
        material_id=work_order.material_id,
        order_type=work_order.order_type.value,
        order_status=work_order.order_status.value,
        planned_quantity=work_order.planned_quantity,
        actual_quantity=work_order.actual_quantity,
        start_date_planned=work_order.start_date_planned,
        start_date_actual=work_order.start_date_actual,
        end_date_planned=work_order.end_date_planned,
        end_date_actual=work_order.end_date_actual,
        priority=work_order.priority,
        created_by_user_id=work_order.created_by_user_id,
        created_at=work_order.created_at,
        updated_at=work_order.updated_at,
        operations=[
            WorkOrderOperationResponse.model_validate(op) for op in work_order.operations
        ] if work_order.operations else [],
        materials=[
            WorkOrderMaterialResponse.model_validate(mat) for mat in work_order.materials
        ] if work_order.materials else [],
    )


def generate_work_order_number(org_id: int, plant_id: int) -> str:
    """Generate unique work order number (simple sequential for now)"""
    import uuid
    # In production, use database sequence or more sophisticated logic
    return f"WO{org_id}{plant_id}{uuid.uuid4().hex[:8].upper()}"


@router.post(
    "/",
    response_model=WorkOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new work order",
    description="Create a new production work order with validation. Requires material_id, planned_quantity, and priority.",
    responses={
        201: {"description": "Work order created successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Material not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders"],
)
def create_work_order(
    work_order_data: WorkOrderCreateRequest,
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    material_repo: MaterialRepository = Depends(get_material_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Create a new work order.

    - **material_id**: Material ID for finished good (must exist)
    - **order_type**: PRODUCTION, REWORK, or ASSEMBLY (default: PRODUCTION)
    - **planned_quantity**: Planned production quantity (must be positive)
    - **start_date_planned**: Optional planned start date
    - **end_date_planned**: Optional planned end date
    - **priority**: Priority 1-10, where 10 is highest (default: 5)
    """
    try:
        logger.info(f"Creating work order for material {work_order_data.material_id} (user: {user_context['id']})")

        # Verify material exists
        material = material_repo.get_by_id(work_order_data.material_id)
        if not material:
            logger.warning(f"Material not found: {work_order_data.material_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

        # Generate work order number
        org_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")
        work_order_number = generate_work_order_number(org_id, plant_id)

        # Create work order
        wo_dict = {
            "organization_id": org_id,
            "plant_id": plant_id,
            "work_order_number": work_order_number,
            "material_id": work_order_data.material_id,
            "order_type": work_order_data.order_type.value,
            "order_status": "PLANNED",  # Always start as PLANNED
            "planned_quantity": work_order_data.planned_quantity,
            "actual_quantity": 0.0,
            "start_date_planned": work_order_data.start_date_planned,
            "end_date_planned": work_order_data.end_date_planned,
            "priority": work_order_data.priority,
            "created_by_user_id": user_context.get("id"),
        }

        db_work_order = repository.create(wo_dict)

        logger.info(f"Work order created successfully: {db_work_order.work_order_number}")
        return map_work_order_to_response(db_work_order)

    except ValueError as e:
        # Domain validation error or duplicate work order number
        if "already exists" in str(e):
            logger.warning(f"Duplicate work order number")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to create work order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create work order")


@router.get(
    "/{work_order_id}",
    response_model=WorkOrderResponse,
    summary="Get work order by ID",
    description="Retrieve a work order by its ID with operations and materials. RLS filtering is automatic.",
    responses={
        200: {"description": "Work order found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Work order not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders"],
)
def get_work_order(
    work_order_id: int,
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Get work order by ID.

    RLS filtering is automatically applied from the authenticated user's organization/plant context.
    Returns work order with all operations and materials.
    """
    try:
        logger.info(f"Fetching work order with ID: {work_order_id}")

        db_work_order = repository.get_by_id(work_order_id)

        if not db_work_order:
            logger.warning(f"Work order not found: {work_order_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

        return map_work_order_to_response(db_work_order)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch work order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch work order")


@router.get(
    "/",
    response_model=WorkOrderListResponse,
    summary="List work orders with pagination",
    description="List work orders with pagination and optional filters (status, material_id, priority, date range).",
    responses={
        200: {"description": "Work order list retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders"],
)
def list_work_orders(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    material_id: Optional[int] = Query(None, description="Filter by material ID"),
    priority: Optional[int] = Query(None, ge=1, le=10, description="Filter by priority (1-10)"),
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    List work orders with pagination and filters.

    Automatically filtered by authenticated user's organization/plant (RLS).
    """
    try:
        logger.info(f"Listing work orders: page={page}, page_size={page_size}")

        org_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        # Build filters dict
        filters = {}
        if status is not None:
            filters["status"] = status.value
        if material_id is not None:
            filters["material_id"] = material_id
        if priority is not None:
            filters["priority"] = priority

        # Get work orders from repository
        result = repository.list_by_organization(
            org_id=org_id,
            plant_id=plant_id,
            filters=filters if filters else None,
            page=page,
            page_size=page_size,
        )

        # Map work orders to response DTOs
        items = [map_work_order_to_response(work_order) for work_order in result["items"]]

        return WorkOrderListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list work orders: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list work orders")


@router.put(
    "/{work_order_id}",
    response_model=WorkOrderResponse,
    summary="Update work order",
    description="Update an existing work order. Supports partial updates (only provided fields are updated).",
    responses={
        200: {"description": "Work order updated successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Work order not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders"],
)
def update_work_order(
    work_order_id: int,
    update_data: WorkOrderUpdateRequest,
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Update work order by ID.

    Only provided fields will be updated (partial updates supported).
    Work order number, organization_id, and plant_id cannot be updated.
    """
    try:
        logger.info(f"Updating work order: {work_order_id}")

        # Convert Pydantic model to dict, excluding unset fields
        update_dict = update_data.model_dump(exclude_unset=True)

        # Update work order via repository
        db_work_order = repository.update(work_order_id, update_dict)

        logger.info(f"Work order updated successfully: {work_order_id}")
        return map_work_order_to_response(db_work_order)

    except ValueError as e:
        # Work order not found or validation error
        if "not found" in str(e):
            logger.warning(f"Work order not found: {work_order_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to update work order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update work order")


@router.delete(
    "/{work_order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel work order (soft delete)",
    description="Cancel a work order by setting status=CANCELLED. Cannot cancel completed work orders.",
    responses={
        204: {"description": "Work order cancelled successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Work order not found"},
        409: {"model": ConflictErrorResponse, "description": "Already cancelled or cannot cancel"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders"],
)
def cancel_work_order(
    work_order_id: int,
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Cancel work order by ID (soft delete).

    Sets status=CANCELLED instead of physically deleting the record.
    Cannot cancel completed work orders.
    """
    try:
        logger.info(f"Cancelling work order: {work_order_id}")

        success = repository.cancel(work_order_id)

        if not success:
            logger.warning(f"Work order not found: {work_order_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

        logger.info(f"Work order cancelled successfully: {work_order_id}")
        return None

    except ValueError as e:
        # Already cancelled or completed
        logger.warning(f"Cannot cancel work order {work_order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel work order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel work order")


@router.post(
    "/{work_order_id}/release",
    response_model=WorkOrderResponse,
    summary="Release work order",
    description="Release a work order for production (PLANNED -> RELEASED).",
    responses={
        200: {"description": "Work order released successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Work order not found"},
        409: {"model": ConflictErrorResponse, "description": "Invalid state transition"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders", "Production Planning"],
)
def release_work_order(
    work_order_id: int,
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Release work order for production (PLANNED -> RELEASED).

    Can only release work orders in PLANNED status.
    """
    try:
        logger.info(f"Releasing work order: {work_order_id}")

        db_work_order = repository.release(work_order_id)

        logger.info(f"Work order released successfully: {work_order_id}")
        return map_work_order_to_response(db_work_order)

    except ValueError as e:
        # Work order not found or invalid state
        if "not found" in str(e):
            logger.warning(f"Work order not found: {work_order_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.warning(f"Invalid state transition: {e}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to release work order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to release work order")


@router.post(
    "/{work_order_id}/start",
    response_model=WorkOrderResponse,
    summary="Start production",
    description="Start production for a work order (RELEASED -> IN_PROGRESS).",
    responses={
        200: {"description": "Work order started successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Work order not found"},
        409: {"model": ConflictErrorResponse, "description": "Invalid state transition"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders", "Production Planning"],
)
def start_work_order(
    work_order_id: int,
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Start production for work order (RELEASED -> IN_PROGRESS).

    Can only start work orders in RELEASED status.
    Sets start_date_actual to current timestamp.
    """
    try:
        logger.info(f"Starting work order: {work_order_id}")

        db_work_order = repository.start(work_order_id)

        logger.info(f"Work order started successfully: {work_order_id}")
        return map_work_order_to_response(db_work_order)

    except ValueError as e:
        # Work order not found or invalid state
        if "not found" in str(e):
            logger.warning(f"Work order not found: {work_order_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.warning(f"Invalid state transition: {e}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to start work order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start work order")


@router.post(
    "/{work_order_id}/complete",
    response_model=WorkOrderResponse,
    summary="Complete work order",
    description="Complete a work order (IN_PROGRESS -> COMPLETED).",
    responses={
        200: {"description": "Work order completed successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Work order not found"},
        409: {"model": ConflictErrorResponse, "description": "Invalid state transition"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders", "Production Planning"],
)
def complete_work_order(
    work_order_id: int,
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Complete work order (IN_PROGRESS -> COMPLETED).

    Can only complete work orders in IN_PROGRESS status.
    Sets end_date_actual to current timestamp.
    """
    try:
        logger.info(f"Completing work order: {work_order_id}")

        db_work_order = repository.complete(work_order_id)

        logger.info(f"Work order completed successfully: {work_order_id}")
        return map_work_order_to_response(db_work_order)

    except ValueError as e:
        # Work order not found or invalid state
        if "not found" in str(e):
            logger.warning(f"Work order not found: {work_order_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.warning(f"Invalid state transition: {e}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to complete work order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete work order")


@router.post(
    "/{work_order_id}/operations",
    response_model=WorkOrderOperationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add operation to work order",
    description="Add a new operation to a work order.",
    responses={
        201: {"description": "Operation added successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Work order not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders", "Production Planning"],
)
def add_work_order_operation(
    work_order_id: int,
    operation_data: WorkOrderOperationCreateRequest,
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Add operation to work order.

    - **operation_number**: Operation sequence number (must be positive and unique per work order)
    - **operation_name**: Operation name/description
    - **work_center_id**: Work center ID where operation is performed
    - **setup_time_minutes**: Setup time in minutes (default: 0)
    - **run_time_per_unit_minutes**: Run time per unit in minutes (default: 0)
    """
    try:
        logger.info(f"Adding operation to work order {work_order_id}")

        operation_dict = operation_data.model_dump()
        db_operation = repository.add_operation(work_order_id, operation_dict)

        logger.info(f"Operation added successfully to work order {work_order_id}")
        return WorkOrderOperationResponse.model_validate(db_operation)

    except ValueError as e:
        # Work order not found or validation error
        if "not found" in str(e):
            logger.warning(f"Work order not found: {work_order_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to add operation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add operation")


@router.post(
    "/{work_order_id}/materials",
    response_model=WorkOrderMaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add material consumption to work order",
    description="Add a material consumption record to a work order.",
    responses={
        201: {"description": "Material added successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Work order or material not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Work Orders", "Production Planning"],
)
def add_work_order_material(
    work_order_id: int,
    material_data: WorkOrderMaterialCreateRequest,
    repository: WorkOrderRepository = Depends(get_work_order_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Add material consumption to work order.

    - **material_id**: Material ID to be consumed
    - **planned_quantity**: Planned consumption quantity (must be positive)
    - **unit_of_measure_id**: Unit of measure ID
    - **backflush**: Auto-consume on completion (default: False)
    """
    try:
        logger.info(f"Adding material to work order {work_order_id}")

        material_dict = material_data.model_dump()
        db_wo_material = repository.add_material(work_order_id, material_dict)

        logger.info(f"Material added successfully to work order {work_order_id}")
        return WorkOrderMaterialResponse.model_validate(db_wo_material)

    except ValueError as e:
        # Work order or material not found or validation error
        if "not found" in str(e):
            logger.warning(f"Resource not found: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to add material: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add material")
