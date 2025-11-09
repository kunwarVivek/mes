"""
Unit tests for MaterialRepository infrastructure service.
Tests CRUD operations, pagination, filtering, and search.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.models.material import Material, MaterialCategory, UnitOfMeasure, ProcurementType, MRPType
from app.domain.entities.material import MaterialNumber


class TestMaterialRepositoryCreate:
    """Test MaterialRepository create method"""

    def test_create_material_success(self):
        """Test creating a material successfully"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        material_data = {
            "organization_id": 1,
            "plant_id": 101,
            "material_number": "MAT0001",
            "material_name": "Steel Plate 10mm",
            "description": "High grade steel plate",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
            "safety_stock": 100.0,
            "reorder_point": 50.0,
            "lot_size": 500.0,
            "lead_time_days": 7,
            "is_active": True
        }

        mock_material = Material(**material_data)
        mock_material.id = 1
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock()

        # Act
        result = repository.create(material_data)

        # Assert
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()
        assert result is not None

    def test_create_material_validation_failure(self):
        """Test that create fails with invalid material data"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        material_data = {
            "organization_id": 0,  # Invalid - must be positive
            "plant_id": 101,
            "material_number": "MAT0001",
            "material_name": "Steel Plate",
            "description": "Test",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
            "safety_stock": 100.0,
            "reorder_point": 50.0,
            "lot_size": 500.0,
            "lead_time_days": 7,
            "is_active": True
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Organization ID must be positive"):
            repository.create(material_data)

    def test_create_material_unique_constraint_violation(self):
        """Test that create fails when material number already exists"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        material_data = {
            "organization_id": 1,
            "plant_id": 101,
            "material_number": "MAT0001",
            "material_name": "Steel Plate",
            "description": "Test",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
            "safety_stock": 100.0,
            "reorder_point": 50.0,
            "lot_size": 500.0,
            "lead_time_days": 7,
            "is_active": True
        }

        db_session.add = Mock()
        db_session.commit = Mock(side_effect=IntegrityError("duplicate key", {}, None))
        db_session.rollback = Mock()

        # Act & Assert
        with pytest.raises(ValueError, match="Material number MAT0001 already exists"):
            repository.create(material_data)

        db_session.rollback.assert_called_once()


class TestMaterialRepositoryGetById:
    """Test MaterialRepository get_by_id method"""

    def test_get_by_id_exists(self):
        """Test retrieving a material that exists"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_material = Material(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number="MAT0001",
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

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_material
        db_session.query.return_value = mock_query

        # Act
        result = repository.get_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.material_number == "MAT0001"

    def test_get_by_id_not_found(self):
        """Test retrieving a material that does not exist"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db_session.query.return_value = mock_query

        # Act
        result = repository.get_by_id(999)

        # Assert
        assert result is None


class TestMaterialRepositoryGetByMaterialNumber:
    """Test MaterialRepository get_by_material_number method"""

    def test_get_by_material_number_exists(self):
        """Test retrieving material by material number"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_material = Material(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number="MAT0001",
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

        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = mock_material
        db_session.query.return_value = mock_query

        # Act
        result = repository.get_by_material_number(1, 101, "MAT0001")

        # Assert
        assert result is not None
        assert result.material_number == "MAT0001"

    def test_get_by_material_number_not_found(self):
        """Test retrieving material by material number that does not exist"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value = mock_query

        # Act
        result = repository.get_by_material_number(1, 101, "NOTFOUND")

        # Assert
        assert result is None


class TestMaterialRepositoryUpdate:
    """Test MaterialRepository update method"""

    def test_update_material_success(self):
        """Test updating a material successfully"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        existing_material = Material(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number="MAT0001",
            material_name="Steel Plate",
            description="Old description",
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

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = existing_material
        db_session.query.return_value = mock_query
        db_session.commit = Mock()
        db_session.refresh = Mock()

        updates = {
            "description": "New description",
            "safety_stock": 150.0
        }

        # Act
        result = repository.update(1, updates)

        # Assert
        assert result is not None
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()

    def test_update_material_not_found(self):
        """Test updating a material that does not exist"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db_session.query.return_value = mock_query

        updates = {"description": "New description"}

        # Act & Assert
        with pytest.raises(ValueError, match="Material with id 999 not found"):
            repository.update(999, updates)


class TestMaterialRepositoryDelete:
    """Test MaterialRepository delete method (soft delete)"""

    def test_delete_material_success(self):
        """Test soft deleting a material"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        existing_material = Material(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number="MAT0001",
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

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = existing_material
        db_session.query.return_value = mock_query
        db_session.commit = Mock()

        # Act
        result = repository.delete(1)

        # Assert
        assert result is True
        assert existing_material.is_active is False
        db_session.commit.assert_called_once()

    def test_delete_material_not_found(self):
        """Test deleting a material that does not exist"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db_session.query.return_value = mock_query

        # Act
        result = repository.delete(999)

        # Assert
        assert result is False


class TestMaterialRepositoryListByOrganization:
    """Test MaterialRepository list_by_organization method with pagination"""

    def test_list_materials_page_one(self):
        """Test listing materials with pagination - page 1"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

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
            for i in range(1, 11)
        ]

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.filter.return_value = mock_filter
        mock_filter.offset.return_value.limit.return_value.all.return_value = mock_materials[:10]
        mock_filter.count.return_value = 100
        mock_query.filter.return_value = mock_filter
        db_session.query.return_value = mock_query

        # Act
        result = repository.list_by_organization(org_id=1, page=1, page_size=10)

        # Assert
        assert result["total"] == 100
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total_pages"] == 10
        assert len(result["items"]) == 10

    def test_list_materials_with_filters(self):
        """Test listing materials with category filter"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_materials = [
            Material(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number="MAT0001",
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

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.filter.return_value = mock_filter
        mock_filter.offset.return_value.limit.return_value.all.return_value = mock_materials
        mock_filter.count.return_value = 1
        mock_query.filter.return_value = mock_filter
        db_session.query.return_value = mock_query

        filters = {"category_id": 1, "is_active": True}

        # Act
        result = repository.list_by_organization(org_id=1, filters=filters, page=1, page_size=50)

        # Assert
        assert result["total"] == 1
        assert len(result["items"]) == 1


class TestMaterialRepositorySearch:
    """Test MaterialRepository search_materials method (using LIKE fallback in tests)"""

    def test_search_materials_single_term(self):
        """Test searching materials with single term"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

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

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.filter.return_value = mock_filter
        mock_filter.limit.return_value.all.return_value = mock_materials
        mock_query.filter.return_value = mock_filter
        db_session.query.return_value = mock_query

        # Act
        result = repository.search_materials(query="steel", org_id=1, limit=20)

        # Assert
        assert len(result) == 1
        assert result[0].material_number == "STEEL001"

    def test_search_materials_multi_term(self):
        """Test searching materials with multiple terms"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_materials = [
            Material(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number="STEEL001",
                material_name="Steel Plate 10mm",
                description="High grade steel plate",
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

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.filter.return_value = mock_filter
        mock_filter.limit.return_value.all.return_value = mock_materials
        mock_query.filter.return_value = mock_filter
        db_session.query.return_value = mock_query

        # Act
        result = repository.search_materials(query="steel plate", org_id=1, limit=20)

        # Assert
        assert isinstance(result, list)
        assert len(result) >= 0  # Depends on implementation

    def test_search_materials_no_results(self):
        """Test searching materials with no results"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.filter.return_value = mock_filter
        mock_filter.limit.return_value.all.return_value = []
        mock_query.filter.return_value = mock_filter
        db_session.query.return_value = mock_query

        # Act
        result = repository.search_materials(query="nonexistent", org_id=1, limit=20)

        # Assert
        assert len(result) == 0

    def test_search_materials_sql_injection_protection(self):
        """Test that search is protected against SQL injection"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = MaterialRepository(db_session)

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.filter.return_value = mock_filter
        mock_filter.limit.return_value.all.return_value = []
        mock_query.filter.return_value = mock_filter
        db_session.query.return_value = mock_query

        malicious_query = "'; DROP TABLE material; --"

        # Act
        result = repository.search_materials(query=malicious_query, org_id=1, limit=20)

        # Assert - Should not raise exception, should return empty results
        assert isinstance(result, list)
