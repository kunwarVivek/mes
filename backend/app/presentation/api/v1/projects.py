"""
Projects API Router - REST endpoints for project management.

Provides CRUD operations for multi-project manufacturing.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.application.dtos.project_dto import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse
)
from app.infrastructure.repositories.project_repository import ProjectRepository
from app.domain.entities.project import ProjectStatus

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(dto: ProjectCreateRequest, db: Session = Depends(get_db)):
    """
    Create new project.

    Args:
        dto: Project creation data
        db: Database session

    Returns:
        Created project

    Raises:
        409: If project_code already exists in plant
        400: If validation fails
    """
    repo = ProjectRepository(db)
    try:
        project = repo.create(dto)
        return project
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=ProjectListResponse)
def list_projects(
    plant_id: Optional[int] = Query(None, description="Filter by plant ID"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by project status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List projects with filters and pagination.

    Args:
        plant_id: Optional plant filter
        status: Optional status filter
        page: Page number (default: 1)
        page_size: Items per page (default: 10, max: 100)
        db: Database session

    Returns:
        Paginated list of projects
    """
    repo = ProjectRepository(db)
    return repo.list_all(plant_id=plant_id, status=status, page=page, page_size=page_size)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """
    Get single project by ID.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Project details

    Raises:
        404: If project not found
    """
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    dto: ProjectUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update project.

    Args:
        project_id: Project ID
        dto: Update data
        db: Database session

    Returns:
        Updated project

    Raises:
        404: If project not found
        400: If validation fails
    """
    repo = ProjectRepository(db)
    try:
        project = repo.update(project_id, dto)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        return project
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    Soft delete project (set is_active=False).

    Args:
        project_id: Project ID
        db: Database session

    Raises:
        404: If project not found
    """
    repo = ProjectRepository(db)
    success = repo.delete(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
