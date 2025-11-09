"""
MaterialRepository - Infrastructure layer repository for Material entities.

Handles database operations for Material master data with:
- CRUD operations with domain validation
- RLS-aware queries (context set automatically by get_db())
- Pagination and filtering
- Full-text search using pg_search (BM25) or LIKE fallback
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, func
import logging

from app.models.material import Material, ProcurementType, MRPType
from app.domain.entities.material import MaterialDomain, MaterialNumber


logger = logging.getLogger(__name__)


class MaterialRepository:
    """
    Repository for Material entity persistence.

    Provides CRUD operations and search functionality.
    RLS context is automatically applied from database session.
    """

    def __init__(self, db: Session, use_pg_search: bool = False):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session with RLS context
            use_pg_search: Use pg_search extension (default: False for testing)
        """
        self._db = db
        self._use_pg_search = use_pg_search

    def create(self, material_data: dict) -> Material:
        """
        Create new material with domain validation.

        Args:
            material_data: Dictionary with material attributes

        Returns:
            Created Material entity

        Raises:
            ValueError: If validation fails or material number exists
        """
        # Domain validation
        mat_number = MaterialNumber(material_data["material_number"])
        domain_material = MaterialDomain(
            id=None,
            organization_id=material_data["organization_id"],
            plant_id=material_data["plant_id"],
            material_number=mat_number,
            material_name=material_data["material_name"],
            description=material_data.get("description", ""),
            material_category_id=material_data["material_category_id"],
            base_uom_id=material_data["base_uom_id"],
            procurement_type=material_data["procurement_type"],
            mrp_type=material_data["mrp_type"],
            safety_stock=material_data.get("safety_stock", 0.0),
            reorder_point=material_data.get("reorder_point", 0.0),
            lot_size=material_data.get("lot_size", 1.0),
            lead_time_days=material_data.get("lead_time_days", 0),
            is_active=material_data.get("is_active", True)
        )

        # Create database model
        db_material = Material(
            organization_id=material_data["organization_id"],
            plant_id=material_data["plant_id"],
            material_number=mat_number.value,
            material_name=material_data["material_name"],
            description=material_data.get("description", ""),
            material_category_id=material_data["material_category_id"],
            base_uom_id=material_data["base_uom_id"],
            procurement_type=ProcurementType(material_data["procurement_type"]),
            mrp_type=MRPType(material_data["mrp_type"]),
            safety_stock=material_data.get("safety_stock", 0.0),
            reorder_point=material_data.get("reorder_point", 0.0),
            lot_size=material_data.get("lot_size", 1.0),
            lead_time_days=material_data.get("lead_time_days", 0),
            is_active=material_data.get("is_active", True)
        )

        try:
            self._db.add(db_material)
            self._db.commit()
            self._db.refresh(db_material)
            logger.info(f"Created material: {db_material.material_number}")
            return db_material
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to create material: {e}")
            raise ValueError(f"Material number {mat_number.value} already exists")

    def get_by_id(self, material_id: int) -> Optional[Material]:
        """
        Retrieve material by ID.

        RLS filtering is automatic from session context.

        Args:
            material_id: Material ID

        Returns:
            Material entity or None if not found
        """
        return self._db.query(Material).filter(Material.id == material_id).first()

    def get_by_material_number(
        self, org_id: int, plant_id: int, material_number: str
    ) -> Optional[Material]:
        """
        Retrieve material by unique material number within org/plant.

        Args:
            org_id: Organization ID
            plant_id: Plant ID
            material_number: Material number (unique)

        Returns:
            Material entity or None if not found
        """
        return (
            self._db.query(Material)
            .filter(Material.organization_id == org_id)
            .filter(Material.plant_id == plant_id)
            .filter(Material.material_number == material_number)
            .first()
        )

    def update(self, material_id: int, updates: dict) -> Material:
        """
        Update material with validation.

        Args:
            material_id: Material ID to update
            updates: Dictionary with fields to update

        Returns:
            Updated Material entity

        Raises:
            ValueError: If material not found or validation fails
        """
        db_material = self._db.query(Material).filter(Material.id == material_id).first()
        if not db_material:
            raise ValueError(f"Material with id {material_id} not found")

        # Update allowed fields
        updatable_fields = [
            "material_name",
            "description",
            "material_category_id",
            "procurement_type",
            "mrp_type",
            "safety_stock",
            "reorder_point",
            "lot_size",
            "lead_time_days",
            "is_active",
        ]

        for field, value in updates.items():
            if field in updatable_fields:
                if field in ["procurement_type", "mrp_type"]:
                    # Convert to enum
                    setattr(db_material, field, ProcurementType(value) if field == "procurement_type" else MRPType(value))
                else:
                    setattr(db_material, field, value)

        self._db.commit()
        self._db.refresh(db_material)
        logger.info(f"Updated material: {db_material.material_number}")
        return db_material

    def delete(self, material_id: int) -> bool:
        """
        Soft delete material (set is_active=False).

        Args:
            material_id: Material ID to delete

        Returns:
            True if deleted, False if not found
        """
        db_material = self._db.query(Material).filter(Material.id == material_id).first()
        if not db_material:
            return False

        db_material.is_active = False
        self._db.commit()
        logger.info(f"Soft deleted material: {db_material.material_number}")
        return True

    def list_by_organization(
        self,
        org_id: int,
        plant_id: Optional[int] = None,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        List materials with pagination and filtering.

        Args:
            org_id: Organization ID
            plant_id: Optional plant ID filter
            filters: Optional filters (category_id, procurement_type, mrp_type, is_active)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with items, total, page, page_size, total_pages
        """
        query = self._db.query(Material).filter(Material.organization_id == org_id)

        if plant_id is not None:
            query = query.filter(Material.plant_id == plant_id)

        # Apply filters
        if filters:
            if "category_id" in filters:
                query = query.filter(Material.material_category_id == filters["category_id"])
            if "procurement_type" in filters:
                query = query.filter(Material.procurement_type == ProcurementType(filters["procurement_type"]))
            if "mrp_type" in filters:
                query = query.filter(Material.mrp_type == MRPType(filters["mrp_type"]))
            if "is_active" in filters:
                query = query.filter(Material.is_active == filters["is_active"])

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def search_materials(
        self,
        query: str,
        org_id: int,
        plant_id: Optional[int] = None,
        limit: int = 20,
    ) -> List[Material]:
        """
        Full-text search for materials using pg_search (BM25) or LIKE fallback.

        In production: Uses ParadeDB pg_search with BM25 ranking.
        In tests: Uses LIKE queries as fallback.

        Args:
            query: Search query string
            org_id: Organization ID
            plant_id: Optional plant ID filter
            limit: Maximum results to return

        Returns:
            List of Material entities (sorted by relevance if pg_search enabled)
        """
        if not query or not query.strip():
            return []

        # Sanitize query (basic protection)
        query = query.strip()

        # SECURITY FIX: Escape LIKE special characters to prevent SQL injection
        # Must escape backslash FIRST to prevent escape bypass attacks
        # Then escape percent and underscore wildcards
        query_escaped = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        search_pattern = f"%{query_escaped}%"

        db_query = self._db.query(Material).filter(Material.organization_id == org_id)

        if plant_id is not None:
            db_query = db_query.filter(Material.plant_id == plant_id)

        if self._use_pg_search:
            # Production: Use pg_search BM25 (requires ParadeDB extension)
            # This would use: SELECT * FROM material_search_idx WHERE material_search_idx @@@ query
            # For now, we'll use LIKE as fallback since pg_search isn't available in tests
            logger.warning("pg_search not implemented yet, falling back to LIKE search")

            # SECURITY: Use escape parameter to properly handle escaped characters
            db_query = db_query.filter(
                or_(
                    Material.material_number.ilike(search_pattern, escape='\\'),
                    Material.material_name.ilike(search_pattern, escape='\\'),
                    Material.description.ilike(search_pattern, escape='\\'),
                )
            )
        else:
            # Test/Fallback: Use LIKE queries (case-insensitive) with proper escaping
            # SECURITY: Use escape parameter to properly handle escaped characters
            db_query = db_query.filter(
                or_(
                    Material.material_number.ilike(search_pattern, escape='\\'),
                    Material.material_name.ilike(search_pattern, escape='\\'),
                    Material.description.ilike(search_pattern, escape='\\'),
                )
            )

        results = db_query.limit(limit).all()
        logger.info(f"Search query '{query}' returned {len(results)} results")
        return results
