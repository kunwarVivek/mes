"""
MaterialSearchService - Application service for material search.

Provides search functionality with filtering and result formatting.
Coordinates between repository and presentation layers.
"""
from typing import Optional, List, Dict
import logging

from app.infrastructure.repositories.material_repository import MaterialRepository
from app.models.material import Material


logger = logging.getLogger(__name__)


class MaterialSearchService:
    """
    Application service for material search operations.

    Combines repository search with filtering and formats results
    for presentation layer.
    """

    def __init__(self, repository: MaterialRepository):
        """
        Initialize service with material repository.

        Args:
            repository: MaterialRepository instance
        """
        self._repository = repository

    def search(
        self,
        query: str,
        organization_id: int,
        plant_id: Optional[int] = None,
        filters: Optional[dict] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Search materials with filters and format results.

        Args:
            query: Search query string
            organization_id: Organization ID for RLS
            plant_id: Optional plant ID filter
            filters: Optional filters (category_id, procurement_type, mrp_type, is_active)
            limit: Maximum results to return

        Returns:
            List of material dictionaries with search results
        """
        if not query or not query.strip():
            logger.debug("Empty search query, returning empty results")
            return []

        # Get materials from repository
        materials = self._repository.search_materials(
            query=query, org_id=organization_id, plant_id=plant_id, limit=limit
        )

        # Apply additional filters (post-search filtering)
        if filters:
            materials = self._apply_filters(materials, filters)

        # Format results for presentation
        results = [self._format_material(material) for material in materials]

        logger.info(
            f"Search completed: query='{query}', org={organization_id}, "
            f"plant={plant_id}, results={len(results)}"
        )

        return results

    def _apply_filters(self, materials: List[Material], filters: dict) -> List[Material]:
        """
        Apply post-search filters to material list.

        Args:
            materials: List of Material entities
            filters: Filter dictionary

        Returns:
            Filtered list of materials
        """
        filtered = materials

        if "category_id" in filters:
            filtered = [
                m for m in filtered if m.material_category_id == filters["category_id"]
            ]

        if "procurement_type" in filters:
            filtered = [
                m for m in filtered if m.procurement_type.value == filters["procurement_type"]
            ]

        if "mrp_type" in filters:
            filtered = [m for m in filtered if m.mrp_type.value == filters["mrp_type"]]

        if "is_active" in filters:
            filtered = [m for m in filtered if m.is_active == filters["is_active"]]

        return filtered

    def _format_material(self, material: Material) -> Dict:
        """
        Format Material entity as dictionary for API response.

        Args:
            material: Material entity

        Returns:
            Dictionary with material attributes
        """
        return {
            "id": material.id,
            "organization_id": material.organization_id,
            "plant_id": material.plant_id,
            "material_number": material.material_number,
            "material_name": material.material_name,
            "description": material.description,
            "material_category_id": material.material_category_id,
            "base_uom_id": material.base_uom_id,
            "procurement_type": material.procurement_type.value,
            "mrp_type": material.mrp_type.value,
            "safety_stock": material.safety_stock,
            "reorder_point": material.reorder_point,
            "lot_size": material.lot_size,
            "lead_time_days": material.lead_time_days,
            "is_active": material.is_active,
            "created_at": material.created_at.isoformat() if material.created_at else None,
            "updated_at": material.updated_at.isoformat() if material.updated_at else None,
        }
