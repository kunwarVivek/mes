"""
OrganizationRepository - Infrastructure layer repository for Organization entities.

Handles database operations for Organization master data with:
- CRUD operations with domain validation
- Pagination and filtering
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.models.organization import Organization


logger = logging.getLogger(__name__)


class OrganizationRepository:
    """
    Repository for Organization entity persistence.

    Provides CRUD operations and search functionality.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self._db = db

    def create(self, org_data: dict) -> Organization:
        """
        Create new organization.

        Args:
            org_data: Dictionary with organization attributes

        Returns:
            Created Organization entity

        Raises:
            ValueError: If validation fails or org_code exists
        """
        db_org = Organization(
            org_code=org_data["org_code"],
            org_name=org_data["org_name"],
            subdomain=org_data.get("subdomain"),
            is_active=org_data.get("is_active", True)
        )

        try:
            self._db.add(db_org)
            self._db.commit()
            self._db.refresh(db_org)
            logger.info(f"Created organization: {db_org.org_code}")
            return db_org
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to create organization: {e}")
            error_msg = str(e).lower()
            # Check for subdomain constraint first (since subdomain can be None)
            if "subdomain" in error_msg and org_data.get("subdomain"):
                raise ValueError(f"Subdomain {org_data.get('subdomain')} already exists")
            elif "org_code" in error_msg or "unique constraint" in error_msg:
                raise ValueError(f"Organization code {org_data['org_code']} already exists")
            else:
                raise ValueError("Failed to create organization due to integrity constraint")

    def get_by_id(self, org_id: int) -> Optional[Organization]:
        """
        Retrieve organization by ID.

        Args:
            org_id: Organization ID

        Returns:
            Organization entity or None if not found
        """
        return self._db.query(Organization).filter(Organization.id == org_id).first()

    def get_by_org_code(self, org_code: str) -> Optional[Organization]:
        """
        Retrieve organization by unique org_code.

        Args:
            org_code: Organization code (unique)

        Returns:
            Organization entity or None if not found
        """
        return self._db.query(Organization).filter(Organization.org_code == org_code).first()

    def update(self, org_id: int, updates: dict) -> Organization:
        """
        Update organization with validation.

        Args:
            org_id: Organization ID to update
            updates: Dictionary with fields to update

        Returns:
            Updated Organization entity

        Raises:
            ValueError: If organization not found or validation fails
        """
        db_org = self._db.query(Organization).filter(Organization.id == org_id).first()
        if not db_org:
            raise ValueError(f"Organization with id {org_id} not found")

        # Update allowed fields
        updatable_fields = ["org_name", "subdomain", "is_active"]

        for field, value in updates.items():
            if field in updatable_fields:
                setattr(db_org, field, value)

        try:
            self._db.commit()
            self._db.refresh(db_org)
            logger.info(f"Updated organization: {db_org.org_code}")
            return db_org
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to update organization: {e}")
            if "subdomain" in str(e):
                raise ValueError(f"Subdomain {updates.get('subdomain')} already exists")
            else:
                raise ValueError("Failed to update organization due to integrity constraint")

    def delete(self, org_id: int) -> bool:
        """
        Soft delete organization (set is_active=False).

        Args:
            org_id: Organization ID to delete

        Returns:
            True if deleted, False if not found
        """
        db_org = self._db.query(Organization).filter(Organization.id == org_id).first()
        if not db_org:
            return False

        db_org.is_active = False
        self._db.commit()
        logger.info(f"Soft deleted organization: {db_org.org_code}")
        return True

    def list_all(
        self,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        List organizations with pagination and filtering.

        Args:
            filters: Optional filters (is_active)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with items, total, page, page_size, total_pages
        """
        query = self._db.query(Organization)

        # Apply filters
        if filters:
            if "is_active" in filters:
                query = query.filter(Organization.is_active == filters["is_active"])

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.order_by(Organization.org_code).offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
