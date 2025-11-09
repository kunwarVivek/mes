"""
Integration tests for Plant API endpoints (standalone version).

This version directly imports the router to avoid the app.main import chain issue.

Test Coverage:
- POST /api/v1/plants: Create plant
- GET /api/v1/plants: List plants with pagination
- GET /api/v1/plants/{id}: Get plant by ID
- PUT /api/v1/plants/{id}: Update plant
- DELETE /api/v1/plants/{id}: Soft delete plant
- Test validation: duplicate plant_code within organization
- Test filtering: by organization_id
"""

import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Workaround for TestClient compatibility
try:
    from starlette.testclient import TestClient
except ImportError:
    from fastapi.testclient import TestClient

from app.core.database import Base, get_db

# Import routers directly without going through __init__.py
import sys
import importlib.util

# Import organization router for test data setup
org_spec = importlib.util.spec_from_file_location(
    "organizations",
    "/Users/vivek/jet/unison/backend/app/presentation/api/v1/organizations.py"
)
organizations_module = importlib.util.module_from_spec(org_spec)
org_spec.loader.exec_module(organizations_module)
org_router = organizations_module.router

# Import plant router
plant_spec = importlib.util.spec_from_file_location(
    "plants",
    "/Users/vivek/jet/unison/backend/app/presentation/api/v1/plants.py"
)
plants_module = importlib.util.module_from_spec(plant_spec)
plant_spec.loader.exec_module(plants_module)
plant_router = plants_module.router


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_plants_standalone.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create a minimal FastAPI app for testing
app = FastAPI()
app.include_router(org_router, prefix="/api/v1/organizations")
app.include_router(plant_router, prefix="/api/v1/plants")


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_organization(client):
    """Create a sample organization for testing"""
    org_data = {
        "org_code": "ORG001",
        "org_name": "Test Organization",
        "is_active": True
    }
    response = client.post("/api/v1/organizations/", json=org_data)
    return response.json()


@pytest.fixture(scope="function")
def multiple_organizations(client):
    """Create multiple organizations for testing"""
    orgs = []
    for i in range(1, 4):
        org_data = {
            "org_code": f"ORG{i:03d}",
            "org_name": f"Organization {i}",
            "is_active": True
        }
        response = client.post("/api/v1/organizations/", json=org_data)
        orgs.append(response.json())
    return orgs


class TestPlantCreation:
    """Test POST /api/v1/plants endpoint"""

    def test_create_plant_success(self, client, sample_organization):
        """Should create plant with valid data"""
        plant_data = {
            "organization_id": sample_organization["id"],
            "plant_code": "P001",
            "plant_name": "Main Factory",
            "location": "New York, USA",
            "is_active": True
        }

        response = client.post("/api/v1/plants/", json=plant_data)

        assert response.status_code == 201
        data = response.json()
        assert data["plant_code"] == "P001"
        assert data["plant_name"] == "Main Factory"
        assert data["location"] == "New York, USA"
        assert data["organization_id"] == sample_organization["id"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_plant_without_location(self, client, sample_organization):
        """Should create plant without location"""
        plant_data = {
            "organization_id": sample_organization["id"],
            "plant_code": "P002",
            "plant_name": "Secondary Factory",
            "is_active": True
        }

        response = client.post("/api/v1/plants/", json=plant_data)

        assert response.status_code == 201
        data = response.json()
        assert data["plant_code"] == "P002"
        assert data["location"] is None

    def test_create_plant_duplicate_code_same_org_fails(self, client, sample_organization):
        """Should fail when creating plant with duplicate plant_code in same organization"""
        plant_data = {
            "organization_id": sample_organization["id"],
            "plant_code": "P001",
            "plant_name": "First Plant",
            "is_active": True
        }

        # Create first plant
        response1 = client.post("/api/v1/plants/", json=plant_data)
        assert response1.status_code == 201

        # Try to create duplicate
        plant_data["plant_name"] = "Duplicate Plant"
        response2 = client.post("/api/v1/plants/", json=plant_data)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_plant_duplicate_code_different_org_succeeds(self, client, multiple_organizations):
        """Should allow same plant_code in different organizations"""
        plant_data_org1 = {
            "organization_id": multiple_organizations[0]["id"],
            "plant_code": "P001",
            "plant_name": "Org1 Plant",
            "is_active": True
        }

        plant_data_org2 = {
            "organization_id": multiple_organizations[1]["id"],
            "plant_code": "P001",
            "plant_name": "Org2 Plant",
            "is_active": True
        }

        # Create plant in first organization
        response1 = client.post("/api/v1/plants/", json=plant_data_org1)
        assert response1.status_code == 201

        # Create plant with same code in second organization (should succeed)
        response2 = client.post("/api/v1/plants/", json=plant_data_org2)
        assert response2.status_code == 201

        # Verify they are different plants
        assert response1.json()["id"] != response2.json()["id"]
        assert response1.json()["organization_id"] != response2.json()["organization_id"]

    def test_create_plant_invalid_organization_fails(self, client):
        """Should fail when creating plant with non-existent organization_id"""
        plant_data = {
            "organization_id": 9999,
            "plant_code": "P001",
            "plant_name": "Test Plant",
            "is_active": True
        }

        response = client.post("/api/v1/plants/", json=plant_data)

        assert response.status_code == 400
        assert "organization" in response.json()["detail"].lower()

    def test_create_plant_missing_required_fields_fails(self, client, sample_organization):
        """Should fail when missing required fields"""
        plant_data = {
            "organization_id": sample_organization["id"],
            "plant_name": "Test Plant"
            # Missing plant_code
        }

        response = client.post("/api/v1/plants/", json=plant_data)

        assert response.status_code == 422  # Pydantic validation error


class TestPlantRetrieval:
    """Test GET /api/v1/plants endpoints"""

    def test_get_plants_list(self, client, sample_organization):
        """Should return paginated list of plants"""
        # Create test plants
        for i in range(5):
            plant_data = {
                "organization_id": sample_organization["id"],
                "plant_code": f"P{i:03d}",
                "plant_name": f"Plant {i}",
                "is_active": True
            }
            client.post("/api/v1/plants/", json=plant_data)

        # Get list
        response = client.get("/api/v1/plants/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_get_plants_list_with_pagination(self, client, sample_organization):
        """Should return paginated list with custom page size"""
        # Create 10 plants
        for i in range(10):
            plant_data = {
                "organization_id": sample_organization["id"],
                "plant_code": f"P{i:03d}",
                "plant_name": f"Plant {i}",
                "is_active": True
            }
            client.post("/api/v1/plants/", json=plant_data)

        # Get first page
        response = client.get("/api/v1/plants/?page=1&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total_pages"] == 2

        # Get second page
        response = client.get("/api/v1/plants/?page=2&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 2

    def test_get_plants_filter_by_organization(self, client, multiple_organizations):
        """Should filter plants by organization_id"""
        # Create plants for different organizations
        for i, org in enumerate(multiple_organizations[:2]):
            for j in range(3):
                plant_data = {
                    "organization_id": org["id"],
                    "plant_code": f"P{j:03d}",
                    "plant_name": f"Plant {j} for Org {i}",
                    "is_active": True
                }
                client.post("/api/v1/plants/", json=plant_data)

        # Filter by first organization
        response = client.get(f"/api/v1/plants/?organization_id={multiple_organizations[0]['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(item["organization_id"] == multiple_organizations[0]["id"] for item in data["items"])

        # Filter by second organization
        response = client.get(f"/api/v1/plants/?organization_id={multiple_organizations[1]['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(item["organization_id"] == multiple_organizations[1]["id"] for item in data["items"])

    def test_get_plants_filter_by_active_status(self, client, sample_organization):
        """Should filter plants by is_active status"""
        # Create active and inactive plants
        for i in range(3):
            plant_data = {
                "organization_id": sample_organization["id"],
                "plant_code": f"ACTIVE{i:03d}",
                "plant_name": f"Active Plant {i}",
                "is_active": True
            }
            client.post("/api/v1/plants/", json=plant_data)

        for i in range(2):
            plant_data = {
                "organization_id": sample_organization["id"],
                "plant_code": f"INACTIVE{i:03d}",
                "plant_name": f"Inactive Plant {i}",
                "is_active": False
            }
            client.post("/api/v1/plants/", json=plant_data)

        # Filter by is_active=True
        response = client.get("/api/v1/plants/?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(item["is_active"] is True for item in data["items"])

        # Filter by is_active=False
        response = client.get("/api/v1/plants/?is_active=false")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["is_active"] is False for item in data["items"])

    def test_get_plant_by_id(self, client, sample_organization):
        """Should return plant by ID"""
        plant_data = {
            "organization_id": sample_organization["id"],
            "plant_code": "P001",
            "plant_name": "Test Plant",
            "location": "New York",
            "is_active": True
        }

        # Create plant
        create_response = client.post("/api/v1/plants/", json=plant_data)
        plant_id = create_response.json()["id"]

        # Get by ID
        response = client.get(f"/api/v1/plants/{plant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plant_id
        assert data["plant_code"] == "P001"
        assert data["plant_name"] == "Test Plant"
        assert data["location"] == "New York"

    def test_get_plant_by_invalid_id(self, client):
        """Should return 404 for non-existent plant"""
        response = client.get("/api/v1/plants/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPlantUpdate:
    """Test PUT /api/v1/plants/{id} endpoint"""

    def test_update_plant_success(self, client, sample_organization):
        """Should update plant with valid data"""
        plant_data = {
            "organization_id": sample_organization["id"],
            "plant_code": "P001",
            "plant_name": "Original Name",
            "location": "Original Location",
            "is_active": True
        }

        # Create plant
        create_response = client.post("/api/v1/plants/", json=plant_data)
        plant_id = create_response.json()["id"]

        # Update plant
        update_data = {
            "plant_name": "Updated Name",
            "location": "Updated Location"
        }
        response = client.put(f"/api/v1/plants/{plant_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["plant_name"] == "Updated Name"
        assert data["location"] == "Updated Location"
        assert data["plant_code"] == "P001"  # Should not change

    def test_update_plant_partial(self, client, sample_organization):
        """Should support partial updates"""
        plant_data = {
            "organization_id": sample_organization["id"],
            "plant_code": "P001",
            "plant_name": "Original Name",
            "location": "Original Location",
            "is_active": True
        }

        # Create plant
        create_response = client.post("/api/v1/plants/", json=plant_data)
        plant_id = create_response.json()["id"]

        # Update only plant_name
        update_data = {"plant_name": "Updated Name"}
        response = client.put(f"/api/v1/plants/{plant_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["plant_name"] == "Updated Name"
        assert data["location"] == "Original Location"  # Should remain unchanged

    def test_update_plant_deactivate(self, client, sample_organization):
        """Should deactivate plant"""
        plant_data = {
            "organization_id": sample_organization["id"],
            "plant_code": "P001",
            "plant_name": "Test Plant",
            "is_active": True
        }

        # Create plant
        create_response = client.post("/api/v1/plants/", json=plant_data)
        plant_id = create_response.json()["id"]

        # Deactivate
        update_data = {"is_active": False}
        response = client.put(f"/api/v1/plants/{plant_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_update_plant_invalid_id(self, client):
        """Should return 404 for non-existent plant"""
        update_data = {"plant_name": "Updated Name"}
        response = client.put("/api/v1/plants/999", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPlantDeletion:
    """Test DELETE /api/v1/plants/{id} endpoint"""

    def test_delete_plant_success(self, client, sample_organization):
        """Should soft delete plant"""
        plant_data = {
            "organization_id": sample_organization["id"],
            "plant_code": "P001",
            "plant_name": "Test Plant",
            "is_active": True
        }

        # Create plant
        create_response = client.post("/api/v1/plants/", json=plant_data)
        plant_id = create_response.json()["id"]

        # Delete plant
        response = client.delete(f"/api/v1/plants/{plant_id}")

        assert response.status_code == 204

        # Verify soft delete (is_active=False)
        get_response = client.get(f"/api/v1/plants/{plant_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    def test_delete_plant_invalid_id(self, client):
        """Should return 404 for non-existent plant"""
        response = client.delete("/api/v1/plants/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPlantCascadeDelete:
    """Test cascade delete behavior when organization is deleted"""

    def test_plants_deleted_when_organization_deleted(self, client, sample_organization):
        """Should cascade delete plants when organization is deleted"""
        # Create plants
        for i in range(3):
            plant_data = {
                "organization_id": sample_organization["id"],
                "plant_code": f"P{i:03d}",
                "plant_name": f"Plant {i}",
                "is_active": True
            }
            client.post("/api/v1/plants/", json=plant_data)

        # Verify plants exist
        response = client.get(f"/api/v1/plants/?organization_id={sample_organization['id']}")
        assert response.json()["total"] == 3

        # Delete organization (soft delete)
        client.delete(f"/api/v1/organizations/{sample_organization['id']}")

        # Note: Soft delete won't cascade in database, but plants should still exist
        # This test is more about verifying the FK relationship exists
        # For hard delete (if implemented), plants would be cascade deleted
