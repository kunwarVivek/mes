"""
Organization API Router - Presentation layer endpoints for Organization management.

Provides RESTful API for Organization CRUD operations with:
- Request/response validation via Pydantic
- Pagination and filtering
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.infrastructure.repositories.organization_repository import OrganizationRepository
from app.application.dtos.organization_dto import (
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    OrganizationResponse,
    OrganizationListResponse,
)
from app.models.organization import Organization


logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency to get OrganizationRepository
def get_organization_repository(db: Session = Depends(get_db)) -> OrganizationRepository:
    """Dependency injection for OrganizationRepository"""
    return OrganizationRepository(db)


def map_organization_to_response(org: Organization) -> OrganizationResponse:
    """Map Organization entity to OrganizationResponse DTO"""
    return OrganizationResponse(
        id=org.id,
        org_code=org.org_code,
        org_name=org.org_name,
        subdomain=org.subdomain,
        is_active=org.is_active,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new organization",
    description="Create a new organization with validation. Requires org_code to be unique.",
    tags=["Organizations"],
)
def create_organization(
    org_data: OrganizationCreateRequest,
    repository: OrganizationRepository = Depends(get_organization_repository),
):
    """
    Create a new organization.

    - **org_code**: Unique organization code (uppercase alphanumeric, max 20 chars)
    - **org_name**: Organization name (max 200 chars)
    - **subdomain**: Optional subdomain for white-label access (lowercase alphanumeric with hyphens)
    - **is_active**: Organization active status (default: True)
    """
    try:
        logger.info(f"Creating organization: {org_data.org_code}")

        # Convert Pydantic model to dict for repository
        org_dict = org_data.model_dump()

        # Create organization via repository
        db_org = repository.create(org_dict)

        logger.info(f"Organization created successfully: {db_org.org_code}")
        return map_organization_to_response(db_org)

    except ValueError as e:
        # Domain validation error or duplicate org_code/subdomain
        if "already exists" in str(e):
            logger.warning(f"Duplicate organization: {e}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create organization: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create organization")


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get organization by ID",
    description="Retrieve an organization by its ID.",
    tags=["Organizations"],
)
def get_organization(
    org_id: int,
    repository: OrganizationRepository = Depends(get_organization_repository),
):
    """
    Get organization by ID.
    """
    try:
        logger.info(f"Fetching organization with ID: {org_id}")

        db_org = repository.get_by_id(org_id)

        if not db_org:
            logger.warning(f"Organization not found: {org_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        return map_organization_to_response(db_org)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch organization: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch organization")


@router.put(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
    description="Update an existing organization. Supports partial updates (only provided fields are updated).",
    tags=["Organizations"],
)
def update_organization(
    org_id: int,
    update_data: OrganizationUpdateRequest,
    repository: OrganizationRepository = Depends(get_organization_repository),
):
    """
    Update organization by ID.

    Only provided fields will be updated (partial updates supported).
    Organization code (org_code) cannot be updated.
    """
    try:
        logger.info(f"Updating organization: {org_id}")

        # Convert Pydantic model to dict, excluding unset fields
        update_dict = update_data.model_dump(exclude_unset=True)

        # Update organization via repository
        db_org = repository.update(org_id, update_dict)

        logger.info(f"Organization updated successfully: {org_id}")
        return map_organization_to_response(db_org)

    except ValueError as e:
        # Organization not found or validation error
        if "not found" in str(e):
            logger.warning(f"Organization not found: {org_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to update organization: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update organization")


@router.delete(
    "/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete organization (soft delete)",
    description="Soft delete an organization by setting is_active=False.",
    tags=["Organizations"],
)
def delete_organization(
    org_id: int,
    repository: OrganizationRepository = Depends(get_organization_repository),
):
    """
    Soft delete organization by ID.

    Sets is_active=False instead of physically deleting the record.
    """
    try:
        logger.info(f"Deleting organization: {org_id}")

        success = repository.delete(org_id)

        if not success:
            logger.warning(f"Organization not found: {org_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        logger.info(f"Organization deleted successfully: {org_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete organization: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete organization")


@router.get(
    "/",
    response_model=OrganizationListResponse,
    summary="List organizations with pagination",
    description="List organizations with pagination and optional filters (is_active).",
    tags=["Organizations"],
)
def list_organizations(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    repository: OrganizationRepository = Depends(get_organization_repository),
):
    """
    List organizations with pagination and filters.
    """
    try:
        logger.info(f"Listing organizations: page={page}, page_size={page_size}")

        # Build filters dict
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active

        # Get organizations from repository
        result = repository.list_all(
            filters=filters if filters else None,
            page=page,
            page_size=page_size,
        )

        # Map organizations to response DTOs
        items = [map_organization_to_response(org) for org in result["items"]]

        return OrganizationListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list organizations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list organizations")
