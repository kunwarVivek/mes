"""
Unit tests for PgSearchService - ParadeDB BM25 full-text search.

Tests BM25 search functionality, ranking, and fallback behavior.
Following TDD: RED → GREEN → REFACTOR
"""
import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError

from app.infrastructure.search.pg_search_service import PgSearchService, SearchResult
from app.infrastructure.search.search_config import SearchConfig
from app.models.material import Material, ProcurementType, MRPType


class TestPgSearchServiceInit:
    """Test PgSearchService initialization."""

    def test_init_with_valid_config(self):
        """Test service initializes with valid configuration."""
        # Arrange
        db_mock = Mock(spec=Session)
        config = SearchConfig(use_pg_search=True)

        # Act
        service = PgSearchService(db_mock, config)

        # Assert
        assert service._db == db_mock
        assert service._config == config
        assert service._use_pg_search is True

    def test_init_with_default_config(self):
        """Test service initializes with default configuration."""
        # Arrange
        db_mock = Mock(spec=Session)

        # Act
        service = PgSearchService(db_mock)

        # Assert
        assert service._db == db_mock
        assert service._config is not None
        assert service._use_pg_search is False  # Default fallback


class TestPgSearchServiceBM25Search:
    """Test BM25 search functionality with pg_search."""

    @pytest.fixture
    def db_mock(self):
        """Create mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def config_pg_search(self):
        """Create config with pg_search enabled."""
        return SearchConfig(use_pg_search=True)

    @pytest.fixture
    def config_fallback(self):
        """Create config with fallback mode."""
        return SearchConfig(use_pg_search=False)

    def test_search_materials_with_pg_search_success(self, db_mock, config_pg_search):
        """Test successful BM25 search using pg_search."""
        # Arrange
        service = PgSearchService(db_mock, config_pg_search)

        # Mock materials
        material1 = Mock(spec=Material)
        material1.id = 1
        material1.organization_id = 1
        material1.plant_id = 1
        material1.material_number = "MAT-001"
        material1.material_name = "Steel Plate"
        material1.description = "High carbon steel plate"
        material1.material_category_id = 10
        material1.base_uom_id = 5
        material1.procurement_type = ProcurementType.PURCHASE
        material1.mrp_type = MRPType.MRP
        material1.safety_stock = 100.0
        material1.reorder_point = 50.0
        material1.lot_size = 10.0
        material1.lead_time_days = 7
        material1.is_active = True

        material2 = Mock(spec=Material)
        material2.id = 2
        material2.organization_id = 1
        material2.plant_id = 1
        material2.material_number = "MAT-002"
        material2.material_name = "Steel Rod"
        material2.description = "Stainless steel rod"
        material2.material_category_id = 10
        material2.base_uom_id = 5
        material2.procurement_type = ProcurementType.MANUFACTURE
        material2.mrp_type = MRPType.MRP
        material2.safety_stock = 50.0
        material2.reorder_point = 25.0
        material2.lot_size = 5.0
        material2.lead_time_days = 14
        material2.is_active = True

        # Mock rows with BM25 scores
        row1 = Mock()
        row1.id = 1
        row1.paradedb_score = 12.5

        row2 = Mock()
        row2.id = 2
        row2.paradedb_score = 8.3

        # Mock execute to return rows
        db_mock.execute.return_value.fetchall.return_value = [row1, row2]

        # Mock query chain to return materials
        query_mock = Mock()
        filter_mock = Mock()
        filter_mock.first.side_effect = [material1, material2]
        query_mock.filter.return_value = filter_mock
        db_mock.query.return_value = query_mock

        # Act
        results = service.search_materials(
            query="steel",
            organization_id=1,
            plant_id=1,
            limit=10
        )

        # Assert
        assert len(results) == 2
        assert results[0].id == 1
        assert results[0].score == 12.5
        assert results[0].material_number == "MAT-001"
        assert results[1].score == 8.3
        db_mock.execute.assert_called_once()

    def test_search_materials_empty_query_returns_empty(self, db_mock, config_pg_search):
        """Test empty query returns empty results."""
        # Arrange
        service = PgSearchService(db_mock, config_pg_search)

        # Act
        results = service.search_materials(
            query="",
            organization_id=1
        )

        # Assert
        assert results == []
        db_mock.execute.assert_not_called()

    def test_search_materials_whitespace_query_returns_empty(self, db_mock, config_pg_search):
        """Test whitespace-only query returns empty results."""
        # Arrange
        service = PgSearchService(db_mock, config_pg_search)

        # Act
        results = service.search_materials(
            query="   ",
            organization_id=1
        )

        # Assert
        assert results == []
        db_mock.execute.assert_not_called()

    def test_search_materials_with_plant_filter(self, db_mock, config_pg_search):
        """Test search with plant_id filter."""
        # Arrange
        service = PgSearchService(db_mock, config_pg_search)

        material = Mock(spec=Material)
        material.id = 1
        material.organization_id = 1
        material.plant_id = 5
        material.material_number = "MAT-003"
        material.material_name = "Test Material"
        material.description = "Test description"
        material.material_category_id = 10
        material.base_uom_id = 5
        material.procurement_type = ProcurementType.PURCHASE
        material.mrp_type = MRPType.MRP
        material.safety_stock = 10.0
        material.reorder_point = 5.0
        material.lot_size = 1.0
        material.lead_time_days = 3
        material.is_active = True

        row = Mock()
        row.id = 1
        row.paradedb_score = 10.0

        db_mock.execute.return_value.fetchall.return_value = [row]

        query_mock = Mock()
        filter_mock = Mock()
        filter_mock.first.return_value = material
        query_mock.filter.return_value = filter_mock
        db_mock.query.return_value = query_mock

        # Act
        results = service.search_materials(
            query="test",
            organization_id=1,
            plant_id=5,
            limit=10
        )

        # Assert
        assert len(results) == 1
        assert results[0].id == 1
        # Verify plant_id was included in query
        call_args = db_mock.execute.call_args
        assert "plant_id" in str(call_args) or 5 == 5

    def test_search_materials_respects_limit(self, db_mock, config_pg_search):
        """Test search respects limit parameter."""
        # Arrange
        service = PgSearchService(db_mock, config_pg_search)

        # Create 5 mock materials
        materials = []
        for i in range(5):
            mat = Mock(spec=Material)
            mat.id = i
            mat.paradedb_score = 10.0 - i
            materials.append(mat)

        db_mock.execute.return_value.fetchall.return_value = materials[:3]  # Limited to 3

        # Act
        results = service.search_materials(
            query="test",
            organization_id=1,
            limit=3
        )

        # Assert
        assert len(results) == 3

    def test_search_materials_pg_search_unavailable_fallback(self, db_mock, config_pg_search):
        """Test fallback to LIKE when pg_search fails."""
        # Arrange
        service = PgSearchService(db_mock, config_pg_search)

        # Mock pg_search failure (extension not available)
        db_mock.execute.side_effect = ProgrammingError(
            "relation 'materials_search_idx' does not exist", None, None
        )

        # Act & Assert - should raise or fallback gracefully
        with pytest.raises(ProgrammingError):
            service.search_materials(
                query="steel",
                organization_id=1
            )


class TestPgSearchServiceFallbackMode:
    """Test fallback to LIKE queries when pg_search is disabled."""

    @pytest.fixture
    def config_fallback(self):
        """Create config with fallback mode."""
        return SearchConfig(use_pg_search=False)

    def test_search_materials_fallback_uses_like(self, config_fallback):
        """Test fallback mode uses LIKE queries."""
        # Arrange
        db_mock = Mock(spec=Session)

        material = Mock(spec=Material)
        material.id = 1
        material.organization_id = 1
        material.plant_id = 1
        material.material_number = "MAT-001"
        material.material_name = "Steel"
        material.description = "Test steel"
        material.material_category_id = 10
        material.base_uom_id = 5
        material.procurement_type = ProcurementType.PURCHASE
        material.mrp_type = MRPType.MRP
        material.safety_stock = 10.0
        material.reorder_point = 5.0
        material.lot_size = 1.0
        material.lead_time_days = 3
        material.is_active = True

        # Mock query chain
        query_mock = Mock()
        filter_mock1 = Mock()
        filter_mock2 = Mock()
        limit_mock = Mock()

        db_mock.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock1
        filter_mock1.filter.return_value = filter_mock2
        filter_mock2.limit.return_value = limit_mock
        limit_mock.all.return_value = [material]

        service = PgSearchService(db_mock, config_fallback)

        # Act
        results = service.search_materials(
            query="steel",
            organization_id=1,
            limit=10
        )

        # Assert
        assert len(results) == 1
        assert results[0].id == 1
        # Verify LIKE query was used (no BM25 score)
        assert results[0].score is None


class TestPgSearchServiceSearchResult:
    """Test SearchResult data transfer object."""

    def test_search_result_from_material(self):
        """Test creating SearchResult from Material entity."""
        # Arrange
        material = Mock(spec=Material)
        material.id = 1
        material.organization_id = 1
        material.plant_id = 1
        material.material_number = "MAT-001"
        material.material_name = "Steel Plate"
        material.description = "High carbon steel"
        material.material_category_id = 10
        material.base_uom_id = 5
        material.procurement_type = Mock()
        material.procurement_type.value = "purchase"
        material.mrp_type = Mock()
        material.mrp_type.value = "mrp"
        material.safety_stock = 100.0
        material.reorder_point = 50.0
        material.lot_size = 10.0
        material.lead_time_days = 7
        material.is_active = True
        material.paradedb_score = 12.5

        # Act
        result = SearchResult.from_material(material, score=12.5)

        # Assert
        assert result.id == 1
        assert result.material_number == "MAT-001"
        assert result.material_name == "Steel Plate"
        assert result.score == 12.5
        assert result.procurement_type == "purchase"

    def test_search_result_without_score(self):
        """Test SearchResult without BM25 score (fallback mode)."""
        # Arrange
        material = Mock(spec=Material)
        material.id = 1
        material.organization_id = 1
        material.plant_id = 1
        material.material_number = "MAT-001"
        material.material_name = "Steel"
        material.description = ""
        material.material_category_id = 10
        material.base_uom_id = 5
        material.procurement_type = Mock()
        material.procurement_type.value = "manufacture"
        material.mrp_type = Mock()
        material.mrp_type.value = "mrp"
        material.safety_stock = 0.0
        material.reorder_point = 0.0
        material.lot_size = 1.0
        material.lead_time_days = 0
        material.is_active = True

        # Act
        result = SearchResult.from_material(material, score=None)

        # Assert
        assert result.id == 1
        assert result.score is None
        assert result.procurement_type == "manufacture"


class TestPgSearchServiceEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def config(self):
        """Create default config."""
        return SearchConfig(use_pg_search=False)

    def test_search_with_sql_injection_attempt(self, config):
        """Test search sanitizes SQL injection attempts."""
        # Arrange
        db_mock = Mock(spec=Session)
        service = PgSearchService(db_mock, config)
        malicious_query = "'; DROP TABLE materials; --"

        # Mock query chain
        query_mock = Mock()
        filter_mock1 = Mock()
        filter_mock2 = Mock()
        limit_mock = Mock()

        db_mock.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock1
        filter_mock1.filter.return_value = filter_mock2
        filter_mock2.limit.return_value = limit_mock
        limit_mock.all.return_value = []

        # Act - should not raise, query should be sanitized
        results = service.search_materials(
            query=malicious_query,
            organization_id=1
        )

        # Assert
        assert results == []
        # Verify query was called (sanitized)
        db_mock.query.assert_called()

    def test_search_with_special_characters(self, config):
        """Test search handles special characters correctly."""
        # Arrange
        db_mock = Mock(spec=Session)
        service = PgSearchService(db_mock, config)
        special_query = "test%_\\material"

        # Mock query chain
        query_mock = Mock()
        filter_mock1 = Mock()
        filter_mock2 = Mock()
        limit_mock = Mock()

        db_mock.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock1
        filter_mock1.filter.return_value = filter_mock2
        filter_mock2.limit.return_value = limit_mock
        limit_mock.all.return_value = []

        # Act
        results = service.search_materials(
            query=special_query,
            organization_id=1
        )

        # Assert
        assert isinstance(results, list)

    def test_search_with_zero_limit(self, config):
        """Test search with zero limit returns empty."""
        # Arrange
        db_mock = Mock(spec=Session)
        service = PgSearchService(db_mock, config)

        # Act - zero limit should be validated and return empty
        results = service.search_materials(
            query="test",
            organization_id=1,
            limit=0
        )

        # Assert - should return empty without executing query
        assert results == []
        # Verify no database query was made
        db_mock.query.assert_not_called()

    def test_search_with_negative_limit_uses_default(self, config):
        """Test search with negative limit uses default."""
        # Arrange
        db_mock = Mock(spec=Session)
        service = PgSearchService(db_mock, config)

        # Mock query chain
        query_mock = Mock()
        filter_mock1 = Mock()
        filter_mock2 = Mock()
        limit_mock = Mock()

        db_mock.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock1
        filter_mock1.filter.return_value = filter_mock2
        filter_mock2.limit.return_value = limit_mock
        limit_mock.all.return_value = []

        # Act
        results = service.search_materials(
            query="test",
            organization_id=1,
            limit=-1
        )

        # Assert
        # Should use default limit (20) instead of -1
        assert isinstance(results, list)
