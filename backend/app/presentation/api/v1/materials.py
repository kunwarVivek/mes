"""
Material API Router - Presentation layer endpoints for Material management.

Provides RESTful API for Material CRUD operations with:
- JWT authentication (all endpoints)
- RLS context from authenticated user
- Pagination and filtering
- Full-text search with BM25 ranking
- Request/response validation via Pydantic
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.application.services.material_search_service import MaterialSearchService
from app.application.dtos.material_dto import (
    MaterialCreateRequest,
    MaterialUpdateRequest,
    MaterialResponse,
    MaterialListResponse,
    MaterialSearchResult,
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    BarcodeGenerateRequest,
    BarcodeResponse,
)
from app.models.material import Material, ProcurementType, MRPType
from app.infrastructure.security.dependencies import get_user_context


logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency to get MaterialRepository
def get_material_repository(db: Session = Depends(get_db)) -> MaterialRepository:
    """Dependency injection for MaterialRepository"""
    return MaterialRepository(db, use_pg_search=False)


def map_material_to_response(material: Material) -> MaterialResponse:
    """Map Material entity to MaterialResponse DTO"""
    return MaterialResponse(
        id=material.id,
        organization_id=material.organization_id,
        plant_id=material.plant_id,
        material_number=material.material_number,
        material_name=material.material_name,
        description=material.description,
        material_category_id=material.material_category_id,
        base_uom_id=material.base_uom_id,
        procurement_type=material.procurement_type.value,
        mrp_type=material.mrp_type.value,
        safety_stock=material.safety_stock,
        reorder_point=material.reorder_point,
        lot_size=material.lot_size,
        lead_time_days=material.lead_time_days,
        is_active=material.is_active,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.post(
    "/",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new material",
    description="Create a new material with validation. Requires organization_id, plant_id, and material_number to be unique.",
    responses={
        201: {"description": "Material created successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Material number already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Materials"],
)
def create_material(
    material_data: MaterialCreateRequest,
    repository: MaterialRepository = Depends(get_material_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Create a new material.

    - **organization_id**: Organization ID (must match authenticated user)
    - **plant_id**: Plant ID (must match authenticated user)
    - **material_number**: Unique material number (uppercase alphanumeric, max 10 chars)
    - **material_name**: Material name (max 200 chars)
    - **material_category_id**: Material category ID (foreign key)
    - **base_uom_id**: Base unit of measure ID (foreign key)
    - **procurement_type**: PURCHASE, MANUFACTURE, or BOTH
    - **mrp_type**: MRP or REORDER
    """
    try:
        logger.info(f"Creating material: {material_data.material_number} (user: {user_context['id']})")

        # Convert Pydantic model to dict for repository
        material_dict = material_data.model_dump()

        # Create material via repository
        db_material = repository.create(material_dict)

        logger.info(f"Material created successfully: {db_material.material_number}")
        return map_material_to_response(db_material)

    except ValueError as e:
        # Domain validation error or duplicate material number
        if "already exists" in str(e):
            logger.warning(f"Duplicate material number: {material_data.material_number}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create material: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create material")


@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="Get material by ID",
    description="Retrieve a material by its ID. RLS filtering is automatic.",
    responses={
        200: {"description": "Material found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Material not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Materials"],
)
def get_material(
    material_id: int,
    repository: MaterialRepository = Depends(get_material_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Get material by ID.

    RLS filtering is automatically applied from the authenticated user's organization/plant context.
    """
    try:
        logger.info(f"Fetching material with ID: {material_id}")

        db_material = repository.get_by_id(material_id)

        if not db_material:
            logger.warning(f"Material not found: {material_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

        return map_material_to_response(db_material)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch material: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch material")


@router.get(
    "/number/{material_number}",
    response_model=MaterialResponse,
    summary="Get material by material number",
    description="Retrieve a material by its unique material number within the authenticated user's org/plant.",
    responses={
        200: {"description": "Material found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Material not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Materials"],
)
def get_material_by_number(
    material_number: str,
    repository: MaterialRepository = Depends(get_material_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Get material by unique material number.

    Uses organization_id and plant_id from the authenticated user's JWT token.
    """
    try:
        logger.info(f"Fetching material by number: {material_number}")

        org_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        db_material = repository.get_by_material_number(org_id, plant_id, material_number)

        if not db_material:
            logger.warning(f"Material not found: {material_number}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

        return map_material_to_response(db_material)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch material: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch material")


@router.put(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="Update material",
    description="Update an existing material. Supports partial updates (only provided fields are updated).",
    responses={
        200: {"description": "Material updated successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Material not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Materials"],
)
def update_material(
    material_id: int,
    update_data: MaterialUpdateRequest,
    repository: MaterialRepository = Depends(get_material_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Update material by ID.

    Only provided fields will be updated (partial updates supported).
    Material number, organization_id, and plant_id cannot be updated.
    """
    try:
        logger.info(f"Updating material: {material_id}")

        # Convert Pydantic model to dict, excluding unset fields
        update_dict = update_data.model_dump(exclude_unset=True)

        # Update material via repository
        db_material = repository.update(material_id, update_dict)

        logger.info(f"Material updated successfully: {material_id}")
        return map_material_to_response(db_material)

    except ValueError as e:
        # Material not found or validation error
        if "not found" in str(e):
            logger.warning(f"Material not found: {material_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to update material: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update material")


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete material (soft delete)",
    description="Soft delete a material by setting is_active=False.",
    responses={
        204: {"description": "Material deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Material not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Materials"],
)
def delete_material(
    material_id: int,
    repository: MaterialRepository = Depends(get_material_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Soft delete material by ID.

    Sets is_active=False instead of physically deleting the record.
    """
    try:
        logger.info(f"Deleting material: {material_id}")

        success = repository.delete(material_id)

        if not success:
            logger.warning(f"Material not found: {material_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

        logger.info(f"Material deleted successfully: {material_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete material: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete material")


@router.get(
    "/",
    response_model=MaterialListResponse,
    summary="List materials with pagination",
    description="List materials with pagination and optional filters (category, procurement_type, mrp_type, is_active).",
    responses={
        200: {"description": "Material list retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Materials"],
)
def list_materials(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    category_id: Optional[int] = Query(None, description="Filter by material category ID"),
    procurement_type: Optional[ProcurementType] = Query(None, description="Filter by procurement type"),
    mrp_type: Optional[MRPType] = Query(None, description="Filter by MRP type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    repository: MaterialRepository = Depends(get_material_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    List materials with pagination and filters.

    Automatically filtered by authenticated user's organization/plant (RLS).
    """
    try:
        logger.info(f"Listing materials: page={page}, page_size={page_size}")

        org_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        # Build filters dict
        filters = {}
        if category_id is not None:
            filters["category_id"] = category_id
        if procurement_type is not None:
            filters["procurement_type"] = procurement_type.value
        if mrp_type is not None:
            filters["mrp_type"] = mrp_type.value
        if is_active is not None:
            filters["is_active"] = is_active

        # Get materials from repository
        result = repository.list_by_organization(
            org_id=org_id,
            plant_id=plant_id,
            filters=filters if filters else None,
            page=page,
            page_size=page_size,
        )

        # Map materials to response DTOs
        items = [map_material_to_response(material) for material in result["items"]]

        return MaterialListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list materials: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list materials")


@router.get(
    "/search",
    response_model=List[MaterialSearchResult],
    summary="Search materials using BM25 ranking",
    description="Full-text search for materials using pg_search BM25 ranking (or LIKE fallback in tests).",
    responses={
        200: {"description": "Search results retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Materials"],
)
def search_materials(
    q: str = Query("", description="Search query string"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    repository: MaterialRepository = Depends(get_material_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Search materials using full-text search.

    Searches material_number, material_name, and description fields.
    Results are ranked by relevance (BM25) when pg_search is enabled.
    """
    try:
        logger.info(f"Searching materials: query='{q}', limit={limit}")

        org_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        # Search via repository
        materials = repository.search_materials(
            query=q,
            org_id=org_id,
            plant_id=plant_id,
            limit=limit,
        )

        # Map to response DTOs
        results = [map_material_to_response(material) for material in materials]

        logger.info(f"Search completed: {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Failed to search materials: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search materials")


@router.post(
    "/{material_id}/barcode",
    response_model=BarcodeResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate barcode for material",
    description="Generate barcode and optional QR code for a material. Supports CODE128, CODE39, EAN13, and QR_CODE formats.",
    responses={
        200: {"description": "Barcode generated successfully"},
        400: {"model": ValidationErrorResponse, "description": "Invalid barcode format"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": NotFoundErrorResponse, "description": "Material not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Materials"],
)
def generate_material_barcode(
    material_id: int,
    request: BarcodeGenerateRequest = BarcodeGenerateRequest(),
    repository: MaterialRepository = Depends(get_material_repository),
    user_context: dict = Depends(get_user_context),
):
    """
    Generate barcode for material.

    - **material_id**: Material ID to generate barcode for
    - **format**: Barcode format (CODE128, CODE39, EAN13, QR_CODE) - default CODE128
    - **include_qr**: Include QR code with material details - default False

    Returns Base64-encoded PNG images for barcode and optional QR code.
    """
    try:
        logger.info(f"Generating barcode for material ID: {material_id}, format: {request.format}")

        # Import BarcodeService here to avoid circular imports
        from app.application.services.barcode_service import BarcodeService

        # Create service instance
        barcode_service = BarcodeService(repository)

        # Generate barcode label
        result = barcode_service.generate_material_label(
            material_id=material_id,
            include_qr=request.include_qr
        )

        # Build response
        response_data = {
            "material_number": result["material_number"],
            "format": request.format,
            "barcode_image": result["barcode_image"],
        }

        # Add QR image if present
        if "qr_image" in result:
            response_data["qr_image"] = result["qr_image"]

        logger.info(f"Barcode generated successfully for material: {result['material_number']}")
        return BarcodeResponse(**response_data)

    except ValueError as e:
        # Material not found or invalid format
        if "not found" in str(e):
            logger.warning(f"Material not found: {material_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to generate barcode: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate barcode")
