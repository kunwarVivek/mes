"""
Plant API Router - Presentation layer endpoints for Plant management.

Provides RESTful API for Plant CRUD operations with:
- Request/response validation via Pydantic
- Multi-tenant isolation by organization_id
- Pagination and filtering
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.infrastructure.repositories.plant_repository import PlantRepository
from app.application.dtos.plant_dto import (
    PlantCreateRequest,
    PlantUpdateRequest,
    PlantResponse,
    PlantListResponse,
)
from app.models.plant import Plant


logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency to get PlantRepository
def get_plant_repository(db: Session = Depends(get_db)) -> PlantRepository:
    """Dependency injection for PlantRepository"""
    return PlantRepository(db)


def map_plant_to_response(plant: Plant) -> PlantResponse:
    """Map Plant entity to PlantResponse DTO"""
    return PlantResponse(
        id=plant.id,
        organization_id=plant.organization_id,
        plant_code=plant.plant_code,
        plant_name=plant.plant_name,
        location=plant.location,
        is_active=plant.is_active,
        created_at=plant.created_at,
        updated_at=plant.updated_at,
    )


@router.post(
    "/",
    response_model=PlantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new plant",
    description="Create a new plant within an organization. Plant code must be unique within the organization.",
    tags=["Plants"],
)
def create_plant(
    plant_data: PlantCreateRequest,
    repository: PlantRepository = Depends(get_plant_repository),
):
    """
    Create a new plant.

    - **organization_id**: Organization ID (foreign key, must exist)
    - **plant_code**: Plant code (max 20 chars, unique within organization)
    - **plant_name**: Plant name (max 200 chars)
    - **location**: Optional location (max 500 chars)
    - **is_active**: Plant active status (default: True)
    """
    try:
        logger.info(f"Creating plant: {plant_data.plant_code} for org {plant_data.organization_id}")

        # Convert Pydantic model to dict for repository
        plant_dict = plant_data.model_dump()

        # Create plant via repository
        db_plant = repository.create(plant_dict)

        logger.info(f"Plant created successfully: {db_plant.plant_code}")
        return map_plant_to_response(db_plant)

    except ValueError as e:
        # Domain validation error or duplicate plant_code/invalid org
        if "already exists" in str(e):
            logger.warning(f"Duplicate plant: {e}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif "not found" in str(e):
            logger.warning(f"Invalid organization: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create plant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create plant")


@router.get(
    "/{plant_id}",
    response_model=PlantResponse,
    summary="Get plant by ID",
    description="Retrieve a plant by its ID.",
    tags=["Plants"],
)
def get_plant(
    plant_id: int,
    repository: PlantRepository = Depends(get_plant_repository),
):
    """
    Get plant by ID.
    """
    try:
        logger.info(f"Fetching plant with ID: {plant_id}")

        db_plant = repository.get_by_id(plant_id)

        if not db_plant:
            logger.warning(f"Plant not found: {plant_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")

        return map_plant_to_response(db_plant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch plant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch plant")


@router.put(
    "/{plant_id}",
    response_model=PlantResponse,
    summary="Update plant",
    description="Update an existing plant. Supports partial updates (only provided fields are updated).",
    tags=["Plants"],
)
def update_plant(
    plant_id: int,
    update_data: PlantUpdateRequest,
    repository: PlantRepository = Depends(get_plant_repository),
):
    """
    Update plant by ID.

    Only provided fields will be updated (partial updates supported).
    Plant code (plant_code) and organization_id cannot be updated.
    """
    try:
        logger.info(f"Updating plant: {plant_id}")

        # Convert Pydantic model to dict, excluding unset fields
        update_dict = update_data.model_dump(exclude_unset=True)

        # Update plant via repository
        db_plant = repository.update(plant_id, update_dict)

        logger.info(f"Plant updated successfully: {plant_id}")
        return map_plant_to_response(db_plant)

    except ValueError as e:
        # Plant not found or validation error
        if "not found" in str(e):
            logger.warning(f"Plant not found: {plant_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to update plant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update plant")


@router.delete(
    "/{plant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete plant (soft delete)",
    description="Soft delete a plant by setting is_active=False.",
    tags=["Plants"],
)
def delete_plant(
    plant_id: int,
    repository: PlantRepository = Depends(get_plant_repository),
):
    """
    Soft delete plant by ID.

    Sets is_active=False instead of physically deleting the record.
    """
    try:
        logger.info(f"Deleting plant: {plant_id}")

        success = repository.delete(plant_id)

        if not success:
            logger.warning(f"Plant not found: {plant_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")

        logger.info(f"Plant deleted successfully: {plant_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete plant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete plant")


@router.get(
    "/",
    response_model=PlantListResponse,
    summary="List plants with pagination",
    description="List plants with pagination and optional filters (organization_id, is_active).",
    tags=["Plants"],
)
def list_plants(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    repository: PlantRepository = Depends(get_plant_repository),
):
    """
    List plants with pagination and filters.
    """
    try:
        logger.info(f"Listing plants: page={page}, page_size={page_size}")

        # Build filters dict
        filters = {}
        if organization_id is not None:
            filters["organization_id"] = organization_id
        if is_active is not None:
            filters["is_active"] = is_active

        # Get plants from repository
        result = repository.list_all(
            filters=filters if filters else None,
            page=page,
            page_size=page_size,
        )

        # Map plants to response DTOs
        items = [map_plant_to_response(plant) for plant in result["items"]]

        return PlantListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list plants: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list plants")
