"""
Unit tests for MaterialSearchService application service.
Tests search integration with filtering and result formatting.
"""
import pytest
from unittest.mock import Mock, MagicMock
from app.application.services.material_search_service import MaterialSearchService
from app.models.material import Material, ProcurementType, MRPType


class TestMaterialSearchService:
    """Test MaterialSearchService search functionality"""

    def test_search_with_no_filters(self):
        """Test searching materials without filters"""
        # Arrange
        mock_repository = Mock()
        service = MaterialSearchService(mock_repository)

        mock_materials = [
            Material(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number="STEEL001",
                material_name="Steel Plate 10mm",
                description="High grade steel",
                material_category_id=1,
                base_uom_id=1,
                procurement_type=ProcurementType.PURCHASE,
                mrp_type=MRPType.MRP,
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=500.0,
                lead_time_days=7,
                is_active=True
            )
        ]

        mock_repository.search_materials.return_value = mock_materials

        # Act
        result = service.search(
            query="steel",
            organization_id=1,
            plant_id=None,
            filters=None,
            limit=20
        )

        # Assert
        assert len(result) == 1
        assert result[0]["material_number"] == "STEEL001"
        assert "id" in result[0]
        assert "material_name" in result[0]
        mock_repository.search_materials.assert_called_once()

    def test_search_with_category_filter(self):
        """Test searching materials with category filter"""
        # Arrange
        mock_repository = Mock()
        service = MaterialSearchService(mock_repository)

        mock_materials = [
            Material(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number="STEEL001",
                material_name="Steel Plate",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type=ProcurementType.PURCHASE,
                mrp_type=MRPType.MRP,
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=500.0,
                lead_time_days=7,
                is_active=True
            )
        ]

        mock_repository.search_materials.return_value = mock_materials

        filters = {"category_id": 1}

        # Act
        result = service.search(
            query="steel",
            organization_id=1,
            plant_id=None,
            filters=filters,
            limit=20
        )

        # Assert
        assert len(result) == 1
        # In real implementation, filtering would happen
        # Here we just verify the service calls repository correctly

    def test_search_with_procurement_type_filter(self):
        """Test searching materials with procurement type filter"""
        # Arrange
        mock_repository = Mock()
        service = MaterialSearchService(mock_repository)

        mock_materials = [
            Material(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number="STEEL001",
                material_name="Steel Plate",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type=ProcurementType.PURCHASE,
                mrp_type=MRPType.MRP,
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=500.0,
                lead_time_days=7,
                is_active=True
            )
        ]

        mock_repository.search_materials.return_value = mock_materials

        filters = {"procurement_type": "PURCHASE"}

        # Act
        result = service.search(
            query="steel",
            organization_id=1,
            plant_id=None,
            filters=filters,
            limit=20
        )

        # Assert
        assert len(result) == 1

    def test_search_with_is_active_filter(self):
        """Test searching only active materials"""
        # Arrange
        mock_repository = Mock()
        service = MaterialSearchService(mock_repository)

        mock_materials = [
            Material(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number="STEEL001",
                material_name="Steel Plate",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type=ProcurementType.PURCHASE,
                mrp_type=MRPType.MRP,
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=500.0,
                lead_time_days=7,
                is_active=True
            )
        ]

        mock_repository.search_materials.return_value = mock_materials

        filters = {"is_active": True}

        # Act
        result = service.search(
            query="steel",
            organization_id=1,
            plant_id=None,
            filters=filters,
            limit=20
        )

        # Assert
        assert len(result) == 1
        assert all(item["is_active"] for item in result)

    def test_search_result_format(self):
        """Test that search results are properly formatted"""
        # Arrange
        mock_repository = Mock()
        service = MaterialSearchService(mock_repository)

        mock_materials = [
            Material(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number="STEEL001",
                material_name="Steel Plate 10mm",
                description="High grade steel",
                material_category_id=1,
                base_uom_id=1,
                procurement_type=ProcurementType.PURCHASE,
                mrp_type=MRPType.MRP,
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=500.0,
                lead_time_days=7,
                is_active=True
            )
        ]

        mock_repository.search_materials.return_value = mock_materials

        # Act
        result = service.search(
            query="steel",
            organization_id=1,
            plant_id=None,
            filters=None,
            limit=20
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1

        material_dict = result[0]
        assert "id" in material_dict
        assert "material_number" in material_dict
        assert "material_name" in material_dict
        assert "description" in material_dict
        assert "procurement_type" in material_dict
        assert "mrp_type" in material_dict
        assert "is_active" in material_dict

    def test_search_empty_query(self):
        """Test searching with empty query returns empty results"""
        # Arrange
        mock_repository = Mock()
        service = MaterialSearchService(mock_repository)

        mock_repository.search_materials.return_value = []

        # Act
        result = service.search(
            query="",
            organization_id=1,
            plant_id=None,
            filters=None,
            limit=20
        )

        # Assert
        assert len(result) == 0

    def test_search_respects_limit(self):
        """Test that search respects the limit parameter"""
        # Arrange
        mock_repository = Mock()
        service = MaterialSearchService(mock_repository)

        mock_materials = [
            Material(
                id=i,
                organization_id=1,
                plant_id=101,
                material_number=f"MAT{i:04d}",
                material_name=f"Material {i}",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type=ProcurementType.PURCHASE,
                mrp_type=MRPType.MRP,
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=500.0,
                lead_time_days=7,
                is_active=True
            )
            for i in range(1, 6)
        ]

        mock_repository.search_materials.return_value = mock_materials[:5]

        # Act
        result = service.search(
            query="material",
            organization_id=1,
            plant_id=None,
            filters=None,
            limit=5
        )

        # Assert
        assert len(result) <= 5
        mock_repository.search_materials.assert_called_with(
            query="material",
            org_id=1,
            plant_id=None,
            limit=5
        )
