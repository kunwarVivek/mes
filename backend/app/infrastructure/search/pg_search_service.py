"""
PgSearchService - ParadeDB BM25 full-text search service.

Provides BM25-ranked search using pg_search extension with fallback to LIKE.
Implements infrastructure layer for search operations.
"""
from typing import List, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import text, or_
import logging

from app.infrastructure.search.search_config import SearchConfig
from app.models.material import Material


logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    Search result data transfer object.

    Contains material data with BM25 relevance score.
    """

    id: int
    organization_id: int
    plant_id: int
    material_number: str
    material_name: str
    description: str
    material_category_id: int
    base_uom_id: int
    procurement_type: str
    mrp_type: str
    safety_stock: float
    reorder_point: float
    lot_size: float
    lead_time_days: int
    is_active: bool
    score: Optional[float] = None
    """BM25 relevance score (None if fallback mode)."""

    @classmethod
    def from_material(cls, material: Material, score: Optional[float] = None) -> "SearchResult":
        """
        Create SearchResult from Material entity.

        Args:
            material: Material entity
            score: Optional BM25 score

        Returns:
            SearchResult instance
        """
        return cls(
            id=material.id,
            organization_id=material.organization_id,
            plant_id=material.plant_id,
            material_number=material.material_number,
            material_name=material.material_name,
            description=material.description or "",
            material_category_id=material.material_category_id,
            base_uom_id=material.base_uom_id,
            procurement_type=material.procurement_type.value,
            mrp_type=material.mrp_type.value,
            safety_stock=material.safety_stock or 0.0,
            reorder_point=material.reorder_point or 0.0,
            lot_size=material.lot_size or 1.0,
            lead_time_days=material.lead_time_days or 0,
            is_active=material.is_active,
            score=score,
        )


class PgSearchService:
    """
    Full-text search service using ParadeDB pg_search (BM25).

    Provides BM25-ranked search with fallback to LIKE queries.
    Handles search index management and query execution.
    """

    def __init__(self, db: Session, config: Optional[SearchConfig] = None):
        """
        Initialize search service.

        Args:
            db: SQLAlchemy database session
            config: Search configuration (default: fallback mode)
        """
        self._db = db
        self._config = config or SearchConfig()
        self._use_pg_search = self._config.use_pg_search

    def search_materials(
        self,
        query: str,
        organization_id: int,
        plant_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Search materials using BM25 ranking or LIKE fallback.

        Args:
            query: Search query string
            organization_id: Organization ID for RLS
            plant_id: Optional plant ID filter
            limit: Maximum results (default from config)

        Returns:
            List of SearchResult with BM25 scores (if available)
        """
        # Validate query
        if not query or not query.strip():
            return []

        # Sanitize and normalize query
        query = query.strip()

        # Early return for zero limit
        if limit is not None and limit == 0:
            return []

        # Validate limit
        validated_limit = self._config.validate_limit(limit)

        # Execute search based on configuration
        if self._use_pg_search:
            return self._search_with_pg_search(
                query, organization_id, plant_id, validated_limit
            )
        else:
            return self._search_with_like_fallback(
                query, organization_id, plant_id, validated_limit
            )

    def _search_with_pg_search(
        self,
        query: str,
        organization_id: int,
        plant_id: Optional[int],
        limit: int,
    ) -> List[SearchResult]:
        """
        Execute BM25 search using pg_search extension.

        Uses ParadeDB BM25 index for relevance ranking.

        Args:
            query: Search query
            organization_id: Organization ID
            plant_id: Optional plant filter
            limit: Maximum results

        Returns:
            List of SearchResult with BM25 scores

        Raises:
            ProgrammingError: If pg_search index not available
        """
        # Build pg_search query using ParadeDB syntax
        # SELECT * FROM material WHERE material @@@ 'query' ORDER BY paradedb.score(id) DESC

        sql_query = text("""
            SELECT
                m.*,
                paradedb.score(m.id) as paradedb_score
            FROM material m
            WHERE m.materials_search_idx @@@ :query
                AND m.organization_id = :org_id
                AND (:plant_id IS NULL OR m.plant_id = :plant_id)
            ORDER BY paradedb_score DESC
            LIMIT :limit
        """)

        params = {
            "query": query,
            "org_id": organization_id,
            "plant_id": plant_id,
            "limit": limit,
        }

        try:
            result = self._db.execute(sql_query, params)
            rows = result.fetchall()

            results = []
            for row in rows:
                material = self._db.query(Material).filter(Material.id == row.id).first()
                if material:
                    score = float(row.paradedb_score) if hasattr(row, 'paradedb_score') else None
                    results.append(SearchResult.from_material(material, score=score))

            logger.info(
                f"pg_search query '{query}' returned {len(results)} results "
                f"(org={organization_id}, plant={plant_id})"
            )
            return results

        except ProgrammingError as e:
            logger.error(f"pg_search query failed: {e}")
            raise

    def _search_with_like_fallback(
        self,
        query: str,
        organization_id: int,
        plant_id: Optional[int],
        limit: int,
    ) -> List[SearchResult]:
        """
        Execute fallback search using LIKE queries.

        Used when pg_search is not available (testing, development).

        Args:
            query: Search query
            organization_id: Organization ID
            plant_id: Optional plant filter
            limit: Maximum results

        Returns:
            List of SearchResult without BM25 scores
        """
        # Escape LIKE special characters to prevent SQL injection
        query_escaped = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        search_pattern = f"%{query_escaped}%"

        # Build LIKE query
        db_query = self._db.query(Material).filter(
            Material.organization_id == organization_id
        )

        if plant_id is not None:
            db_query = db_query.filter(Material.plant_id == plant_id)

        # Search across multiple fields
        db_query = db_query.filter(
            or_(
                Material.material_number.ilike(search_pattern, escape='\\'),
                Material.material_name.ilike(search_pattern, escape='\\'),
                Material.description.ilike(search_pattern, escape='\\'),
            )
        )

        materials = db_query.limit(limit).all()

        results = [SearchResult.from_material(m, score=None) for m in materials]

        logger.info(
            f"LIKE fallback query '{query}' returned {len(results)} results "
            f"(org={organization_id}, plant={plant_id})"
        )

        return results
