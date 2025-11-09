"""
Department API Router - Presentation layer endpoints for Department management.

Provides RESTful API for Department CRUD operations with:
- Request/response validation via Pydantic
- Pagination and filtering by plant_id
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.infrastructure.repositories.department_repository import DepartmentRepository
from app.application.dtos.department_dto import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    DepartmentResponse,
    DepartmentListResponse,
)
from app.models.department import Department


logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency to get DepartmentRepository
def get_department_repository(db: Session = Depends(get_db)) -> DepartmentRepository:
    """Dependency injection for DepartmentRepository"""
    return DepartmentRepository(db)


def map_department_to_response(dept: Department) -> DepartmentResponse:
    """Map Department entity to DepartmentResponse DTO"""
    return DepartmentResponse(
        id=dept.id,
        plant_id=dept.plant_id,
        dept_code=dept.dept_code,
        dept_name=dept.dept_name,
        description=dept.description,
        is_active=dept.is_active,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new department",
    description="Create a new department within a plant. dept_code must be unique within the plant.",
    tags=["Departments"],
)
def create_department(
    dept_data: DepartmentCreateRequest,
    repository: DepartmentRepository = Depends(get_department_repository),
):
    """
    Create a new department.

    - **plant_id**: Plant ID (foreign key, required)
    - **dept_code**: Department code (max 20 chars, unique within plant)
    - **dept_name**: Department name (max 200 chars)
    - **description**: Optional description
    - **is_active**: Department active status (default: True)
    """
    try:
        logger.info(f"Creating department: {dept_data.dept_code} for plant {dept_data.plant_id}")

        # Convert Pydantic model to dict for repository
        dept_dict = dept_data.model_dump()

        # Create department via repository
        db_dept = repository.create(dept_dict)

        logger.info(f"Department created successfully: {db_dept.dept_code}")
        return map_department_to_response(db_dept)

    except ValueError as e:
        # Domain validation error or duplicate dept_code/invalid plant_id
        if "already exists" in str(e):
            logger.warning(f"Duplicate department: {e}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create department: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create department")


@router.get(
    "/{dept_id}",
    response_model=DepartmentResponse,
    summary="Get department by ID",
    description="Retrieve a department by its ID.",
    tags=["Departments"],
)
def get_department(
    dept_id: int,
    repository: DepartmentRepository = Depends(get_department_repository),
):
    """
    Get department by ID.
    """
    try:
        logger.info(f"Fetching department with ID: {dept_id}")

        db_dept = repository.get_by_id(dept_id)

        if not db_dept:
            logger.warning(f"Department not found: {dept_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        return map_department_to_response(db_dept)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch department: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch department")


@router.put(
    "/{dept_id}",
    response_model=DepartmentResponse,
    summary="Update department",
    description="Update an existing department. Supports partial updates (only provided fields are updated).",
    tags=["Departments"],
)
def update_department(
    dept_id: int,
    update_data: DepartmentUpdateRequest,
    repository: DepartmentRepository = Depends(get_department_repository),
):
    """
    Update department by ID.

    Only provided fields will be updated (partial updates supported).
    Department code (dept_code) cannot be updated.
    """
    try:
        logger.info(f"Updating department: {dept_id}")

        # Convert Pydantic model to dict, excluding unset fields
        update_dict = update_data.model_dump(exclude_unset=True)

        # Update department via repository
        db_dept = repository.update(dept_id, update_dict)

        logger.info(f"Department updated successfully: {dept_id}")
        return map_department_to_response(db_dept)

    except ValueError as e:
        # Department not found or validation error
        if "not found" in str(e):
            logger.warning(f"Department not found: {dept_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to update department: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update department")


@router.delete(
    "/{dept_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete department (soft delete)",
    description="Soft delete a department by setting is_active=False.",
    tags=["Departments"],
)
def delete_department(
    dept_id: int,
    repository: DepartmentRepository = Depends(get_department_repository),
):
    """
    Soft delete department by ID.

    Sets is_active=False instead of physically deleting the record.
    """
    try:
        logger.info(f"Deleting department: {dept_id}")

        success = repository.delete(dept_id)

        if not success:
            logger.warning(f"Department not found: {dept_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        logger.info(f"Department deleted successfully: {dept_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete department: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete department")


@router.get(
    "/",
    response_model=DepartmentListResponse,
    summary="List departments with pagination",
    description="List departments with pagination and optional filters (plant_id, is_active).",
    tags=["Departments"],
)
def list_departments(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    plant_id: Optional[int] = Query(None, description="Filter by plant ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    repository: DepartmentRepository = Depends(get_department_repository),
):
    """
    List departments with pagination and filters.
    """
    try:
        logger.info(f"Listing departments: page={page}, page_size={page_size}")

        # Build filters dict
        filters = {}
        if plant_id is not None:
            filters["plant_id"] = plant_id
        if is_active is not None:
            filters["is_active"] = is_active

        # Get departments from repository
        result = repository.list_all(
            filters=filters if filters else None,
            page=page,
            page_size=page_size,
        )

        # Map departments to response DTOs
        items = [map_department_to_response(dept) for dept in result["items"]]

        return DepartmentListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list departments: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list departments")
