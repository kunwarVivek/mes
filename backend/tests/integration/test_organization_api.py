"""
Integration tests for Organization API endpoints.

Test Coverage:
- POST /api/v1/organizations: Create organization
- GET /api/v1/organizations: List organizations with pagination
- GET /api/v1/organizations/{id}: Get organization by ID
- PUT /api/v1/organizations/{id}: Update organization
- DELETE /api/v1/organizations/{id}: Soft delete organization
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_organizations.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestOrganizationCreation:
    """Test POST /api/v1/organizations endpoint"""

    def test_create_organization_success(self, client, db_session):
        """Should create organization with valid data"""
        org_data = {
            "org_code": "ORG001",
            "org_name": "Test Organization",
            "subdomain": "test-org",
            "is_active": True
        }

        response = client.post("/api/v1/organizations", json=org_data)

        assert response.status_code == 201
        data = response.json()
        assert data["org_code"] == "ORG001"
        assert data["org_name"] == "Test Organization"
        assert data["subdomain"] == "test-org"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_organization_without_subdomain(self, client, db_session):
        """Should create organization without subdomain"""
        org_data = {
            "org_code": "ORG002",
            "org_name": "Second Organization",
            "is_active": True
        }

        response = client.post("/api/v1/organizations", json=org_data)

        assert response.status_code == 201
        data = response.json()
        assert data["org_code"] == "ORG002"
        assert data["subdomain"] is None

    def test_create_organization_duplicate_code_fails(self, client, db_session):
        """Should fail when creating organization with duplicate org_code"""
        org_data = {
            "org_code": "ORG001",
            "org_name": "First Organization",
            "is_active": True
        }

        # Create first organization
        response1 = client.post("/api/v1/organizations", json=org_data)
        assert response1.status_code == 201

        # Try to create duplicate
        org_data["org_name"] = "Duplicate Organization"
        response2 = client.post("/api/v1/organizations", json=org_data)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_organization_duplicate_subdomain_fails(self, client, db_session):
        """Should fail when creating organization with duplicate subdomain"""
        org_data1 = {
            "org_code": "ORG001",
            "org_name": "First Organization",
            "subdomain": "test-org",
            "is_active": True
        }

        org_data2 = {
            "org_code": "ORG002",
            "org_name": "Second Organization",
            "subdomain": "test-org",
            "is_active": True
        }

        # Create first organization
        response1 = client.post("/api/v1/organizations", json=org_data1)
        assert response1.status_code == 201

        # Try to create with duplicate subdomain
        response2 = client.post("/api/v1/organizations", json=org_data2)

        assert response2.status_code == 409
        assert "subdomain" in response2.json()["detail"].lower()

    def test_create_organization_invalid_code_fails(self, client, db_session):
        """Should fail with invalid org_code format"""
        org_data = {
            "org_code": "org-001",  # Lowercase with hyphen (invalid)
            "org_name": "Test Organization",
            "is_active": True
        }

        response = client.post("/api/v1/organizations", json=org_data)

        assert response.status_code == 422  # Pydantic validation error
        assert "org_code" in str(response.json())

    def test_create_organization_invalid_subdomain_fails(self, client, db_session):
        """Should fail with invalid subdomain format"""
        org_data = {
            "org_code": "ORG001",
            "org_name": "Test Organization",
            "subdomain": "Test_Org",  # Uppercase with underscore (invalid)
            "is_active": True
        }

        response = client.post("/api/v1/organizations", json=org_data)

        assert response.status_code == 422  # Pydantic validation error
        assert "subdomain" in str(response.json())

    def test_create_organization_missing_required_fields(self, client, db_session):
        """Should fail when required fields are missing"""
        org_data = {
            "org_code": "ORG001",
            # Missing org_name
        }

        response = client.post("/api/v1/organizations", json=org_data)

        assert response.status_code == 422  # Validation error


class TestOrganizationRetrieval:
    """Test GET /api/v1/organizations endpoints"""

    def test_get_organizations_list(self, client, db_session):
        """Should return paginated list of organizations"""
        # Create test organizations
        for i in range(5):
            org_data = {
                "org_code": f"ORG{i:03d}",
                "org_name": f"Organization {i}",
                "is_active": True
            }
            client.post("/api/v1/organizations", json=org_data)

        # Get list
        response = client.get("/api/v1/organizations")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_get_organizations_list_with_pagination(self, client, db_session):
        """Should return paginated list with custom page size"""
        # Create 10 organizations
        for i in range(10):
            org_data = {
                "org_code": f"ORG{i:03d}",
                "org_name": f"Organization {i}",
                "is_active": True
            }
            client.post("/api/v1/organizations", json=org_data)

        # Get first page
        response = client.get("/api/v1/organizations?page=1&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total_pages"] == 2

        # Get second page
        response = client.get("/api/v1/organizations?page=2&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 2

    def test_get_organizations_filter_by_active_status(self, client, db_session):
        """Should filter organizations by is_active status"""
        # Create active and inactive organizations
        for i in range(3):
            org_data = {
                "org_code": f"ACTIVE{i:03d}",
                "org_name": f"Active Organization {i}",
                "is_active": True
            }
            client.post("/api/v1/organizations", json=org_data)

        for i in range(2):
            org_data = {
                "org_code": f"INACTIVE{i:03d}",
                "org_name": f"Inactive Organization {i}",
                "is_active": False
            }
            client.post("/api/v1/organizations", json=org_data)

        # Filter by is_active=True
        response = client.get("/api/v1/organizations?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(item["is_active"] is True for item in data["items"])

        # Filter by is_active=False
        response = client.get("/api/v1/organizations?is_active=false")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["is_active"] is False for item in data["items"])

    def test_get_organization_by_id(self, client, db_session):
        """Should return organization by ID"""
        org_data = {
            "org_code": "ORG001",
            "org_name": "Test Organization",
            "subdomain": "test-org",
            "is_active": True
        }

        # Create organization
        create_response = client.post("/api/v1/organizations", json=org_data)
        org_id = create_response.json()["id"]

        # Get by ID
        response = client.get(f"/api/v1/organizations/{org_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == org_id
        assert data["org_code"] == "ORG001"
        assert data["org_name"] == "Test Organization"

    def test_get_organization_by_invalid_id(self, client, db_session):
        """Should return 404 for non-existent organization"""
        response = client.get("/api/v1/organizations/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestOrganizationUpdate:
    """Test PUT /api/v1/organizations/{id} endpoint"""

    def test_update_organization_success(self, client, db_session):
        """Should update organization with valid data"""
        org_data = {
            "org_code": "ORG001",
            "org_name": "Original Name",
            "subdomain": "original",
            "is_active": True
        }

        # Create organization
        create_response = client.post("/api/v1/organizations", json=org_data)
        org_id = create_response.json()["id"]

        # Update organization
        update_data = {
            "org_name": "Updated Name",
            "subdomain": "updated"
        }
        response = client.put(f"/api/v1/organizations/{org_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["org_name"] == "Updated Name"
        assert data["subdomain"] == "updated"
        assert data["org_code"] == "ORG001"  # Should not change

    def test_update_organization_partial(self, client, db_session):
        """Should support partial updates"""
        org_data = {
            "org_code": "ORG001",
            "org_name": "Original Name",
            "subdomain": "original",
            "is_active": True
        }

        # Create organization
        create_response = client.post("/api/v1/organizations", json=org_data)
        org_id = create_response.json()["id"]

        # Update only org_name
        update_data = {"org_name": "Updated Name"}
        response = client.put(f"/api/v1/organizations/{org_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["org_name"] == "Updated Name"
        assert data["subdomain"] == "original"  # Should remain unchanged

    def test_update_organization_deactivate(self, client, db_session):
        """Should deactivate organization"""
        org_data = {
            "org_code": "ORG001",
            "org_name": "Test Organization",
            "is_active": True
        }

        # Create organization
        create_response = client.post("/api/v1/organizations", json=org_data)
        org_id = create_response.json()["id"]

        # Deactivate
        update_data = {"is_active": False}
        response = client.put(f"/api/v1/organizations/{org_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_update_organization_invalid_id(self, client, db_session):
        """Should return 404 for non-existent organization"""
        update_data = {"org_name": "Updated Name"}
        response = client.put("/api/v1/organizations/999", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestOrganizationDeletion:
    """Test DELETE /api/v1/organizations/{id} endpoint"""

    def test_delete_organization_success(self, client, db_session):
        """Should soft delete organization"""
        org_data = {
            "org_code": "ORG001",
            "org_name": "Test Organization",
            "is_active": True
        }

        # Create organization
        create_response = client.post("/api/v1/organizations", json=org_data)
        org_id = create_response.json()["id"]

        # Delete organization
        response = client.delete(f"/api/v1/organizations/{org_id}")

        assert response.status_code == 204

        # Verify soft delete (is_active=False)
        get_response = client.get(f"/api/v1/organizations/{org_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    def test_delete_organization_invalid_id(self, client, db_session):
        """Should return 404 for non-existent organization"""
        response = client.delete("/api/v1/organizations/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
