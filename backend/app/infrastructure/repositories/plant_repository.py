"""
PlantRepository - Infrastructure layer repository for Plant entities.

Handles database operations for Plant master data with:
- CRUD operations with domain validation
- Pagination and filtering
- Multi-tenant isolation by organization_id
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
import logging

from app.models.plant import Plant
from app.models.organization import Organization

logger = logging.getLogger(__name__)


class PlantRepository:
    """
    Repository for Plant entity persistence.

    Provides CRUD operations and search functionality.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self._db = db

    def create(self, plant_data: dict) -> Plant:
        """
        Create new plant.

        Args:
            plant_data: Dictionary with plant attributes

        Returns:
            Created Plant entity

        Raises:
            ValueError: If validation fails, organization doesn't exist, or plant_code exists within org
        """
        # Validate organization exists
        org = self._db.query(Organization).filter(
            Organization.id == plant_data["organization_id"]
        ).first()

        if not org:
            raise ValueError(f"Organization with id {plant_data['organization_id']} not found")

        db_plant = Plant(
            organization_id=plant_data["organization_id"],
            plant_code=plant_data["plant_code"],
            plant_name=plant_data["plant_name"],
            location=plant_data.get("location"),
            is_active=plant_data.get("is_active", True)
        )

        try:
            self._db.add(db_plant)
            self._db.commit()
            self._db.refresh(db_plant)
            logger.info(f"Created plant: {db_plant.plant_code} for org {db_plant.organization_id}")
            return db_plant
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to create plant: {e}")
            error_msg = str(e).lower()
            if "uq_plant_code_per_org" in error_msg or "unique constraint" in error_msg:
                raise ValueError(
                    f"Plant code {plant_data['plant_code']} already exists in organization {plant_data['organization_id']}"
                )
            elif "foreign key" in error_msg:
                raise ValueError(f"Organization with id {plant_data['organization_id']} not found")
            else:
                raise ValueError("Failed to create plant due to integrity constraint")

    def get_by_id(self, plant_id: int) -> Optional[Plant]:
        """
        Retrieve plant by ID.

        Args:
            plant_id: Plant ID

        Returns:
            Plant entity or None if not found
        """
        return self._db.query(Plant).filter(Plant.id == plant_id).first()

    def get_by_plant_code(
        self,
        organization_id: int,
        plant_code: str
    ) -> Optional[Plant]:
        """
        Retrieve plant by unique plant_code within organization.

        Args:
            organization_id: Organization ID
            plant_code: Plant code (unique within organization)

        Returns:
            Plant entity or None if not found
        """
        return self._db.query(Plant).filter(
            and_(
                Plant.organization_id == organization_id,
                Plant.plant_code == plant_code
            )
        ).first()

    def update(self, plant_id: int, updates: dict) -> Plant:
        """
        Update plant with validation.

        Args:
            plant_id: Plant ID to update
            updates: Dictionary with fields to update

        Returns:
            Updated Plant entity

        Raises:
            ValueError: If plant not found or validation fails
        """
        db_plant = self._db.query(Plant).filter(Plant.id == plant_id).first()
        if not db_plant:
            raise ValueError(f"Plant with id {plant_id} not found")

        # Update allowed fields
        updatable_fields = ["plant_name", "location", "is_active"]

        for field, value in updates.items():
            if field in updatable_fields:
                setattr(db_plant, field, value)

        try:
            self._db.commit()
            self._db.refresh(db_plant)
            logger.info(f"Updated plant: {db_plant.plant_code}")
            return db_plant
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to update plant: {e}")
            raise ValueError("Failed to update plant due to integrity constraint")

    def delete(self, plant_id: int) -> bool:
        """
        Soft delete plant (set is_active=False).

        Args:
            plant_id: Plant ID to delete

        Returns:
            True if deleted, False if not found
        """
        db_plant = self._db.query(Plant).filter(Plant.id == plant_id).first()
        if not db_plant:
            return False

        db_plant.is_active = False
        self._db.commit()
        logger.info(f"Soft deleted plant: {db_plant.plant_code}")
        return True

    def list_all(
        self,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        List plants with pagination and filtering.

        Args:
            filters: Optional filters (organization_id, is_active)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with items, total, page, page_size, total_pages
        """
        query = self._db.query(Plant)

        # Apply filters
        if filters:
            if "organization_id" in filters:
                query = query.filter(Plant.organization_id == filters["organization_id"])
            if "is_active" in filters:
                query = query.filter(Plant.is_active == filters["is_active"])

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.order_by(Plant.organization_id, Plant.plant_code).offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
