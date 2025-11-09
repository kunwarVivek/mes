"""
ProjectRepository - Infrastructure layer repository for Project entities.

Handles database operations for Project entities with:
- CRUD operations with domain validation
- Pagination and filtering by plant_id and status
- Duplicate project_code detection per plant
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.models.project import Project
from app.domain.entities.project import ProjectStatus
from app.application.dtos.project_dto import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectListResponse
)

logger = logging.getLogger(__name__)


class ProjectRepository:
    """
    Repository for Project entity persistence.

    Provides CRUD operations and search functionality.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self._db = db

    def create(self, dto: ProjectCreateRequest) -> Project:
        """
        Create new project.

        Args:
            dto: ProjectCreateRequest with project data

        Returns:
            Created Project entity

        Raises:
            ValueError: If validation fails or project_code exists in plant
        """
        # Check if plant exists
        from app.models.plant import Plant
        plant = self._db.query(Plant).filter(Plant.id == dto.plant_id).first()
        if not plant:
            raise ValueError(f"Plant with id {dto.plant_id} not found")

        # Check if organization exists
        from app.models.organization import Organization
        org = self._db.query(Organization).filter(Organization.id == dto.organization_id).first()
        if not org:
            raise ValueError(f"Organization with id {dto.organization_id} not found")

        # Check if BOM exists (if provided)
        if dto.bom_id:
            from app.models.bom import BOMHeader
            bom = self._db.query(BOMHeader).filter(BOMHeader.id == dto.bom_id).first()
            if not bom:
                raise ValueError(f"BOM with id {dto.bom_id} not found")

        db_project = Project(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            project_code=dto.project_code,
            project_name=dto.project_name,
            description=dto.description,
            bom_id=dto.bom_id,
            planned_start_date=dto.planned_start_date,
            planned_end_date=dto.planned_end_date,
            status=dto.status,
            priority=dto.priority,
            is_active=True
        )

        try:
            self._db.add(db_project)
            self._db.commit()
            self._db.refresh(db_project)
            logger.info(f"Created project: {db_project.project_code} in plant {db_project.plant_id}")
            return db_project
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to create project: {e}")
            error_msg = str(e).lower()
            if "uq_project_code_per_plant" in error_msg or "unique constraint" in error_msg:
                raise ValueError(f"Project code {dto.project_code} already exists in plant {dto.plant_id}")
            elif "check_dates" in error_msg:
                raise ValueError("planned_end_date must be >= planned_start_date")
            elif "foreign key" in error_msg:
                raise ValueError("Invalid organization_id, plant_id, or bom_id")
            else:
                raise ValueError("Failed to create project due to integrity constraint")

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """
        Retrieve project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project entity or None if not found
        """
        return self._db.query(Project).filter(Project.id == project_id).first()

    def update(self, project_id: int, dto: ProjectUpdateRequest) -> Optional[Project]:
        """
        Update project with validation.

        Args:
            project_id: Project ID to update
            dto: ProjectUpdateRequest with fields to update

        Returns:
            Updated Project entity or None if not found

        Raises:
            ValueError: If validation fails
        """
        db_project = self._db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return None

        # Update only provided fields
        update_data = dto.model_dump(exclude_unset=True)

        # Validate BOM if being updated
        if "bom_id" in update_data and update_data["bom_id"]:
            from app.models.bom import BOMHeader
            bom = self._db.query(BOMHeader).filter(BOMHeader.id == update_data["bom_id"]).first()
            if not bom:
                raise ValueError(f"BOM with id {update_data['bom_id']} not found")

        for field, value in update_data.items():
            setattr(db_project, field, value)

        try:
            self._db.commit()
            self._db.refresh(db_project)
            logger.info(f"Updated project: {db_project.project_code}")
            return db_project
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to update project: {e}")
            error_msg = str(e).lower()
            if "check_dates" in error_msg:
                raise ValueError("planned_end_date must be >= planned_start_date")
            else:
                raise ValueError("Failed to update project due to integrity constraint")

    def delete(self, project_id: int) -> bool:
        """
        Soft delete project (set is_active=False).

        Args:
            project_id: Project ID to delete

        Returns:
            True if deleted, False if not found
        """
        db_project = self._db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return False

        db_project.is_active = False
        self._db.commit()
        logger.info(f"Soft deleted project: {db_project.project_code}")
        return True

    def list_all(
        self,
        plant_id: Optional[int] = None,
        status: Optional[ProjectStatus] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> ProjectListResponse:
        """
        List projects with pagination and filtering.

        Args:
            plant_id: Optional filter by plant_id
            status: Optional filter by project status
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            ProjectListResponse with items, total, page, page_size
        """
        query = self._db.query(Project)

        # Apply filters
        if plant_id is not None:
            query = query.filter(Project.plant_id == plant_id)
        if status is not None:
            query = query.filter(Project.status == status)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.order_by(Project.project_code).offset(offset).limit(page_size).all()

        return ProjectListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
