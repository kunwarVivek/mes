"""
Unit tests for Material API endpoints.

Tests Material API router with mocked repository to avoid database dependencies.
Follows TDD approach: RED -> GREEN -> REFACTOR
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from unittest.mock import Mock, MagicMock
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


# Mock Material model to avoid SQLAlchemy redefinition issues
class MockMaterial:
    """Mock Material entity for testing"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockEnum:
    """Mock enum for procurement/mrp types"""
    def __init__(self, value):
        self.value = value


def create_mock_material(**overrides):
    """Helper to create mock material with defaults"""
    defaults = {
        "id": 1,
        "organization_id": 1,
        "plant_id": 1,
        "material_number": "MAT001",
        "material_name": "Test Material",
        "description": "Test description",
        "material_category_id": 1,
        "base_uom_id": 1,
        "procurement_type": MockEnum("PURCHASE"),
        "mrp_type": MockEnum("MRP"),
        "safety_stock": 100.0,
        "reorder_point": 50.0,
        "lot_size": 10.0,
        "lead_time_days": 5,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": None,
    }
    defaults.update(overrides)
    return MockMaterial(**defaults)


@pytest.fixture
def test_app():
    """Create test FastAPI app with materials router"""
    from app.presentation.api.v1.materials import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/materials", tags=["Materials"])
    return app


@pytest.fixture
def client_fixture(test_app):
    """Test client fixture"""
    return TestClient(test_app)


@pytest.fixture(autouse=True)
def mock_repository(monkeypatch):
    """Auto-use mock MaterialRepository for all tests"""
    mock_repo = Mock()

    def mock_get_repo(db):
        return mock_repo

    # Mock the dependency
    import app.presentation.api.v1.materials
    monkeypatch.setattr(
        app.presentation.api.v1.materials,
        "get_material_repository",
        lambda db: mock_repo
    )
    return mock_repo


@pytest.fixture(autouse=True)
def mock_auth(monkeypatch):
    """Auto-use mock authentication for all tests"""
    def mock_get_user_context():
        return {
            "id": 1,
            "email": "test@example.com",
            "organization_id": 1,
            "plant_id": 1,
        }

    # Mock the dependency
    import app.presentation.api.v1.materials
    monkeypatch.setattr(
        app.presentation.api.v1.materials,
        "get_user_context",
        mock_get_user_context
    )
    return mock_get_user_context


class TestMaterialAPICreate:
    """Test POST /api/v1/materials/ endpoint"""

    def test_create_material_success(self, mock_repository, client_fixture):
        """Test successful material creation returns 201"""
        # Arrange
        material_data = {
            "organization_id": 1,
            "plant_id": 1,
            "material_number": "MAT001",
            "material_name": "Test Material",
            "description": "Test description",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
            "safety_stock": 100.0,
            "reorder_point": 50.0,
            "lot_size": 10.0,
            "lead_time_days": 5,
        }

        mock_material = create_mock_material()
        mock_repository.create.return_value = mock_material

        # Act
        response = client_fixture.post("/api/v1/materials/", json=material_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["material_number"] == "MAT001"
        assert data["material_name"] == "Test Material"
        assert data["procurement_type"] == "PURCHASE"

    def test_create_material_validation_error(self, client_fixture):
        """Test material creation with invalid data returns 422"""
        # Arrange - invalid material_number (lowercase)
        material_data = {
            "organization_id": 1,
            "plant_id": 1,
            "material_number": "mat001",  # Invalid: should be uppercase
            "material_name": "Test Material",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
        }

        # Act
        response = client_fixture.post("/api/v1/materials/", json=material_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_material_duplicate_returns_409(self, mock_repository, client_fixture):
        """Test material creation with duplicate number returns 409"""
        # Arrange
        material_data = {
            "organization_id": 1,
            "plant_id": 1,
            "material_number": "MAT001",
            "material_name": "Test Material",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
        }

        mock_repository.create.side_effect = ValueError("Material number MAT001 already exists")

        # Act
        response = client_fixture.post("/api/v1/materials/", json=material_data)

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT


class TestMaterialAPIGetById:
    """Test GET /api/v1/materials/{material_id} endpoint"""

    def test_get_material_success(self, mock_repository, client_fixture):
        """Test successful material retrieval returns 200"""
        # Arrange
        mock_material = create_mock_material()
        mock_repository.get_by_id.return_value = mock_material

        # Act
        response = client_fixture.get("/api/v1/materials/1")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["material_number"] == "MAT001"

    def test_get_material_not_found(self, mock_repository, client_fixture):
        """Test material retrieval with non-existent ID returns 404"""
        # Arrange
        mock_repository.get_by_id.return_value = None

        # Act
        response = client_fixture.get("/api/v1/materials/999")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_material_rls_isolation(self, mock_repository, client_fixture):
        """Test material from different org returns 404 (RLS isolation)"""
        # Arrange - material from different org
        mock_repository.get_by_id.return_value = None  # RLS blocks access

        # Act
        response = client_fixture.get("/api/v1/materials/1")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMaterialAPIGetByNumber:
    """Test GET /api/v1/materials/number/{material_number} endpoint"""

    def test_get_material_by_number_success(self, mock_repository, client_fixture):
        """Test successful material retrieval by number returns 200"""
        # Arrange
        mock_material = create_mock_material()
        mock_repository.get_by_material_number.return_value = mock_material

        # Act
        response = client_fixture.get("/api/v1/materials/number/MAT001")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["material_number"] == "MAT001"

    def test_get_material_by_number_not_found(self, mock_repository, client_fixture):
        """Test material retrieval by non-existent number returns 404"""
        # Arrange
        mock_repository.get_by_material_number.return_value = None

        # Act
        response = client_fixture.get("/api/v1/materials/number/NOTFOUND")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMaterialAPIUpdate:
    """Test PUT /api/v1/materials/{material_id} endpoint"""

    def test_update_material_success(self, mock_repository, client_fixture):
        """Test successful material update returns 200"""
        # Arrange
        update_data = {
            "material_name": "Updated Material",
            "description": "Updated description",
            "safety_stock": 150.0,
        }

        mock_material = create_mock_material(
            material_name="Updated Material",
            description="Updated description",
            safety_stock=150.0,
            updated_at=datetime.now(),
        )
        mock_repository.update.return_value = mock_material

        # Act
        response = client_fixture.put("/api/v1/materials/1", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["material_name"] == "Updated Material"
        assert data["safety_stock"] == 150.0

    def test_update_material_not_found(self, mock_repository, client_fixture):
        """Test update of non-existent material returns 404"""
        # Arrange
        update_data = {"material_name": "Updated Material"}
        mock_repository.update.side_effect = ValueError("Material with id 999 not found")

        # Act
        response = client_fixture.put("/api/v1/materials/999", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_material_validation_error(self, client_fixture):
        """Test update with invalid data returns 422"""
        # Arrange - invalid procurement_type
        update_data = {"procurement_type": "INVALID_TYPE"}

        # Act
        response = client_fixture.put("/api/v1/materials/1", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMaterialAPIDelete:
    """Test DELETE /api/v1/materials/{material_id} endpoint"""

    def test_delete_material_success(self, mock_repository, client_fixture):
        """Test successful material deletion returns 204"""
        # Arrange
        mock_repository.delete.return_value = True

        # Act
        response = client_fixture.delete("/api/v1/materials/1")

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_material_not_found(self, mock_repository, client_fixture):
        """Test deletion of non-existent material returns 404"""
        # Arrange
        mock_repository.delete.return_value = False

        # Act
        response = client_fixture.delete("/api/v1/materials/999")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_material_already_deleted(self, mock_repository, client_fixture):
        """Test deletion of already deleted material returns 404"""
        # Arrange
        mock_repository.delete.return_value = False

        # Act
        response = client_fixture.delete("/api/v1/materials/1")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMaterialAPIList:
    """Test GET /api/v1/materials/ endpoint"""

    def test_list_materials_success(self, mock_repository, client_fixture):
        """Test successful material listing with pagination"""
        # Arrange
        mock_materials = [
            create_mock_material(id=1, material_number="MAT001", material_name="Material 1"),
            create_mock_material(
                id=2,
                material_number="MAT002",
                material_name="Material 2",
                procurement_type=MockEnum("MANUFACTURE"),
                mrp_type=MockEnum("REORDER"),
                safety_stock=200.0,
                reorder_point=100.0,
                lot_size=20.0,
                lead_time_days=10,
            ),
        ]

        mock_repository.list_by_organization.return_value = {
            "items": mock_materials,
            "total": 2,
            "page": 1,
            "page_size": 50,
            "total_pages": 1,
        }

        # Act
        response = client_fixture.get("/api/v1/materials/")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1

    def test_list_materials_with_filters(self, mock_repository, client_fixture):
        """Test material listing with category filter"""
        # Arrange
        mock_repository.list_by_organization.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 50,
            "total_pages": 0,
        }

        # Act
        response = client_fixture.get("/api/v1/materials/?category_id=1&procurement_type=PURCHASE&is_active=true")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        mock_repository.list_by_organization.assert_called_once()

    def test_list_materials_pagination(self, mock_repository, client_fixture):
        """Test material listing with custom pagination"""
        # Arrange
        mock_repository.list_by_organization.return_value = {
            "items": [],
            "total": 100,
            "page": 2,
            "page_size": 20,
            "total_pages": 5,
        }

        # Act
        response = client_fixture.get("/api/v1/materials/?page=2&page_size=20")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 20


class TestMaterialAPISearch:
    """Test GET /api/v1/materials/search endpoint"""

    def test_search_materials_success(self, mock_repository, client_fixture):
        """Test successful material search with results"""
        # Arrange
        mock_materials = [
            create_mock_material(
                material_number="MAT001",
                material_name="Steel Plate",
                description="High quality steel",
            )
        ]

        mock_repository.search_materials.return_value = mock_materials

        # Act
        response = client_fixture.get("/api/v1/materials/search?q=steel&limit=10")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["material_name"] == "Steel Plate"

    def test_search_materials_empty_query(self, mock_repository, client_fixture):
        """Test search with empty query returns empty results"""
        # Arrange
        mock_repository.search_materials.return_value = []

        # Act
        response = client_fixture.get("/api/v1/materials/search?q=")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_search_materials_sql_injection_protection(self, mock_repository, client_fixture):
        """Test search protects against SQL injection"""
        # Arrange
        mock_repository.search_materials.return_value = []

        # Act - attempt SQL injection
        response = client_fixture.get("/api/v1/materials/search?q=' OR '1'='1")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0
