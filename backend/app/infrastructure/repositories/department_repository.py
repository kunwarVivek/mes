"""
DepartmentRepository - Infrastructure layer repository for Department entities.

Handles database operations for Department master data with:
- CRUD operations with domain validation
- Pagination and filtering by plant_id
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.models.department import Department

logger = logging.getLogger(__name__)


class DepartmentRepository:
    """
    Repository for Department entity persistence.

    Provides CRUD operations and search functionality.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self._db = db

    def create(self, dept_data: dict) -> Department:
        """
        Create new department.

        Args:
            dept_data: Dictionary with department attributes

        Returns:
            Created Department entity

        Raises:
            ValueError: If validation fails, plant doesn't exist, or dept_code exists in plant
        """
        # Check if plant exists
        from app.models.plant import Plant
        plant = self._db.query(Plant).filter(Plant.id == dept_data["plant_id"]).first()
        if not plant:
            raise ValueError(f"Plant with id {dept_data['plant_id']} not found")

        db_dept = Department(
            plant_id=dept_data["plant_id"],
            dept_code=dept_data["dept_code"],
            dept_name=dept_data["dept_name"],
            description=dept_data.get("description"),
            is_active=dept_data.get("is_active", True)
        )

        try:
            self._db.add(db_dept)
            self._db.commit()
            self._db.refresh(db_dept)
            logger.info(f"Created department: {db_dept.dept_code} in plant {db_dept.plant_id}")
            return db_dept
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to create department: {e}")
            error_msg = str(e).lower()
            if "uq_dept_code_per_plant" in error_msg or "unique constraint" in error_msg:
                raise ValueError(f"Department code {dept_data['dept_code']} already exists in plant {dept_data['plant_id']}")
            elif "foreign key" in error_msg:
                raise ValueError(f"Invalid plant_id {dept_data['plant_id']}")
            else:
                raise ValueError("Failed to create department due to integrity constraint")

    def get_by_id(self, dept_id: int) -> Optional[Department]:
        """
        Retrieve department by ID.

        Args:
            dept_id: Department ID

        Returns:
            Department entity or None if not found
        """
        return self._db.query(Department).filter(Department.id == dept_id).first()

    def update(self, dept_id: int, updates: dict) -> Department:
        """
        Update department with validation.

        Args:
            dept_id: Department ID to update
            updates: Dictionary with fields to update

        Returns:
            Updated Department entity

        Raises:
            ValueError: If department not found or validation fails
        """
        db_dept = self._db.query(Department).filter(Department.id == dept_id).first()
        if not db_dept:
            raise ValueError(f"Department with id {dept_id} not found")

        # Update allowed fields
        updatable_fields = ["dept_name", "description", "is_active"]

        for field, value in updates.items():
            if field in updatable_fields:
                setattr(db_dept, field, value)

        try:
            self._db.commit()
            self._db.refresh(db_dept)
            logger.info(f"Updated department: {db_dept.dept_code}")
            return db_dept
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to update department: {e}")
            raise ValueError("Failed to update department due to integrity constraint")

    def delete(self, dept_id: int) -> bool:
        """
        Soft delete department (set is_active=False).

        Args:
            dept_id: Department ID to delete

        Returns:
            True if deleted, False if not found
        """
        db_dept = self._db.query(Department).filter(Department.id == dept_id).first()
        if not db_dept:
            return False

        db_dept.is_active = False
        self._db.commit()
        logger.info(f"Soft deleted department: {db_dept.dept_code}")
        return True

    def list_all(
        self,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        List departments with pagination and filtering.

        Args:
            filters: Optional filters (plant_id, is_active)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with items, total, page, page_size, total_pages
        """
        query = self._db.query(Department)

        # Apply filters
        if filters:
            if "plant_id" in filters:
                query = query.filter(Department.plant_id == filters["plant_id"])
            if "is_active" in filters:
                query = query.filter(Department.is_active == filters["is_active"])

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.order_by(Department.dept_code).offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
