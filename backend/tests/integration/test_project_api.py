"""
Integration tests for Project API endpoints.

Test Coverage:
- POST /api/v1/projects: Create project
- GET /api/v1/projects: List projects with pagination and filters
- GET /api/v1/projects/{id}: Get project by ID
- PUT /api/v1/projects/{id}: Update project
- DELETE /api/v1/projects/{id}: Soft delete project
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.organization import Organization
from app.models.plant import Plant
from app.models.bom import BOMHeader, BOMType
from app.models.material import Material, MaterialCategory, UnitOfMeasure


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_projects.db"
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


@pytest.fixture
def setup_test_data(db_session):
    """Create test organization, plant, and BOM for projects"""
    # Create organization
    org = Organization(
        org_code="ORG001",
        org_name="Test Organization",
        is_active=True
    )
    db_session.add(org)
    db_session.flush()

    # Create plant
    plant = Plant(
        organization_id=org.id,
        plant_code="PLT001",
        plant_name="Test Plant",
        location="Test Location",
        is_active=True
    )
    db_session.add(plant)
    db_session.flush()

    # Create UoM
    uom = UnitOfMeasure(
        uom_code="EA",
        uom_name="Each",
        uom_category="COUNT",
        is_active=True
    )
    db_session.add(uom)
    db_session.flush()

    # Create material category
    category = MaterialCategory(
        category_code="FG",
        category_name="Finished Goods",
        is_active=True
    )
    db_session.add(category)
    db_session.flush()

    # Create material
    material = Material(
        organization_id=org.id,
        plant_id=plant.id,
        material_number="MAT-001",
        material_name="Test Material",
        material_category_id=category.id,
        base_unit_of_measure_id=uom.id,
        is_active=True
    )
    db_session.add(material)
    db_session.flush()

    # Create BOM
    bom = BOMHeader(
        organization_id=org.id,
        plant_id=plant.id,
        bom_number="BOM-001",
        material_id=material.id,
        bom_version=1,
        bom_name="Test BOM",
        bom_type=BOMType.PRODUCTION,
        base_quantity=1.0,
        unit_of_measure_id=uom.id,
        is_active=True,
        created_by_user_id=1
    )
    db_session.add(bom)
    db_session.commit()

    return {
        "org_id": org.id,
        "plant_id": plant.id,
        "bom_id": bom.id
    }


class TestProjectCreation:
    """Test POST /api/v1/projects endpoint"""

    def test_create_project_success_full(self, client, setup_test_data):
        """Should create project with all fields"""
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-001",
            "project_name": "Manufacturing Project Alpha",
            "description": "First production project",
            "bom_id": setup_test_data["bom_id"],
            "planned_start_date": "2025-01-01",
            "planned_end_date": "2025-12-31",
            "status": "PLANNING",
            "priority": 5
        }

        response = client.post("/api/v1/projects", json=project_data)

        assert response.status_code == 201
        data = response.json()
        assert data["project_code"] == "PROJ-001"
        assert data["project_name"] == "Manufacturing Project Alpha"
        assert data["description"] == "First production project"
        assert data["bom_id"] == setup_test_data["bom_id"]
        assert data["status"] == "PLANNING"
        assert data["priority"] == 5
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_project_minimal(self, client, setup_test_data):
        """Should create project with minimal required fields"""
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-MIN",
            "project_name": "Minimal Project"
        }

        response = client.post("/api/v1/projects", json=project_data)

        assert response.status_code == 201
        data = response.json()
        assert data["project_code"] == "PROJ-MIN"
        assert data["description"] is None
        assert data["bom_id"] is None
        assert data["status"] == "PLANNING"  # Default
        assert data["priority"] == 0  # Default

    def test_create_project_duplicate_code_in_plant_fails(self, client, setup_test_data):
        """Should fail when creating project with duplicate code in same plant"""
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-001",
            "project_name": "First Project"
        }

        # Create first project
        response1 = client.post("/api/v1/projects", json=project_data)
        assert response1.status_code == 201

        # Try to create duplicate
        project_data["project_name"] = "Duplicate Project"
        response2 = client.post("/api/v1/projects", json=project_data)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_project_same_code_different_plant_succeeds(self, client, db_session, setup_test_data):
        """Should allow same project_code in different plants"""
        # Create second plant
        plant2 = Plant(
            organization_id=setup_test_data["org_id"],
            plant_code="PLT002",
            plant_name="Second Plant",
            is_active=True
        )
        db_session.add(plant2)
        db_session.commit()

        # Create project in first plant
        project_data1 = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-001",
            "project_name": "Plant 1 Project"
        }
        response1 = client.post("/api/v1/projects", json=project_data1)
        assert response1.status_code == 201

        # Create project with same code in second plant
        project_data2 = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": plant2.id,
            "project_code": "PROJ-001",  # Same code, different plant
            "project_name": "Plant 2 Project"
        }
        response2 = client.post("/api/v1/projects", json=project_data2)
        assert response2.status_code == 201

    def test_create_project_invalid_dates_fails(self, client, setup_test_data):
        """Should fail when planned_end_date < planned_start_date"""
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-BAD",
            "project_name": "Bad Dates Project",
            "planned_start_date": "2025-12-31",
            "planned_end_date": "2025-01-01"  # Before start
        }

        response = client.post("/api/v1/projects", json=project_data)

        assert response.status_code == 400
        assert "date" in response.json()["detail"].lower()

    def test_create_project_invalid_plant_fails(self, client, setup_test_data):
        """Should fail with non-existent plant_id"""
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": 99999,  # Invalid
            "project_code": "PROJ-001",
            "project_name": "Test Project"
        }

        response = client.post("/api/v1/projects", json=project_data)

        assert response.status_code == 400
        assert "plant" in response.json()["detail"].lower()

    def test_create_project_invalid_bom_fails(self, client, setup_test_data):
        """Should fail with non-existent bom_id"""
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-001",
            "project_name": "Test Project",
            "bom_id": 99999  # Invalid
        }

        response = client.post("/api/v1/projects", json=project_data)

        assert response.status_code == 400
        assert "bom" in response.json()["detail"].lower()


class TestProjectRetrieval:
    """Test GET /api/v1/projects/{id} endpoint"""

    def test_get_project_success(self, client, setup_test_data):
        """Should retrieve project by ID"""
        # Create project
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-GET",
            "project_name": "Get Test Project"
        }
        create_response = client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["id"]

        # Get project
        response = client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["project_code"] == "PROJ-GET"

    def test_get_project_not_found(self, client):
        """Should return 404 for non-existent project"""
        response = client.get("/api/v1/projects/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestProjectList:
    """Test GET /api/v1/projects endpoint"""

    def test_list_projects_empty(self, client, setup_test_data):
        """Should return empty list when no projects exist"""
        response = client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_projects_multiple(self, client, setup_test_data):
        """Should list multiple projects"""
        # Create multiple projects
        for i in range(3):
            project_data = {
                "organization_id": setup_test_data["org_id"],
                "plant_id": setup_test_data["plant_id"],
                "project_code": f"PROJ-{i:03d}",
                "project_name": f"Project {i}"
            }
            client.post("/api/v1/projects", json=project_data)

        response = client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_list_projects_filter_by_plant(self, client, db_session, setup_test_data):
        """Should filter projects by plant_id"""
        # Create second plant
        plant2 = Plant(
            organization_id=setup_test_data["org_id"],
            plant_code="PLT002",
            plant_name="Second Plant",
            is_active=True
        )
        db_session.add(plant2)
        db_session.commit()

        # Create projects in different plants
        project1 = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-P1",
            "project_name": "Plant 1 Project"
        }
        project2 = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": plant2.id,
            "project_code": "PROJ-P2",
            "project_name": "Plant 2 Project"
        }
        client.post("/api/v1/projects", json=project1)
        client.post("/api/v1/projects", json=project2)

        # Filter by first plant
        response = client.get(f"/api/v1/projects?plant_id={setup_test_data['plant_id']}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["plant_id"] == setup_test_data["plant_id"]

    def test_list_projects_filter_by_status(self, client, setup_test_data):
        """Should filter projects by status"""
        # Create projects with different statuses
        project1 = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-PLAN",
            "project_name": "Planning Project",
            "status": "PLANNING"
        }
        project2 = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-ACT",
            "project_name": "Active Project",
            "status": "ACTIVE"
        }
        client.post("/api/v1/projects", json=project1)
        client.post("/api/v1/projects", json=project2)

        # Filter by ACTIVE status
        response = client.get("/api/v1/projects?status=ACTIVE")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "ACTIVE"

    def test_list_projects_pagination(self, client, setup_test_data):
        """Should paginate project list"""
        # Create 15 projects
        for i in range(15):
            project_data = {
                "organization_id": setup_test_data["org_id"],
                "plant_id": setup_test_data["plant_id"],
                "project_code": f"PROJ-{i:03d}",
                "project_name": f"Project {i}"
            }
            client.post("/api/v1/projects", json=project_data)

        # Get first page (default page_size=10)
        response1 = client.get("/api/v1/projects?page=1&page_size=10")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 10
        assert data1["total"] == 15
        assert data1["page"] == 1

        # Get second page
        response2 = client.get("/api/v1/projects?page=2&page_size=10")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 5
        assert data2["total"] == 15
        assert data2["page"] == 2


class TestProjectUpdate:
    """Test PUT /api/v1/projects/{id} endpoint"""

    def test_update_project_success(self, client, setup_test_data):
        """Should update project fields"""
        # Create project
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-UPD",
            "project_name": "Original Name",
            "priority": 1
        }
        create_response = client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["id"]

        # Update project
        update_data = {
            "project_name": "Updated Name",
            "status": "ACTIVE",
            "priority": 10
        }
        response = client.put(f"/api/v1/projects/{project_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == "Updated Name"
        assert data["status"] == "ACTIVE"
        assert data["priority"] == 10
        assert data["project_code"] == "PROJ-UPD"  # Unchanged

    def test_update_project_not_found(self, client):
        """Should return 404 for non-existent project"""
        update_data = {"project_name": "New Name"}
        response = client.put("/api/v1/projects/99999", json=update_data)

        assert response.status_code == 404

    def test_update_project_invalid_dates_fails(self, client, setup_test_data):
        """Should fail when updating with invalid dates"""
        # Create project
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-DATE",
            "project_name": "Date Test"
        }
        create_response = client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["id"]

        # Update with invalid dates
        update_data = {
            "planned_start_date": "2025-12-31",
            "planned_end_date": "2025-01-01"
        }
        response = client.put(f"/api/v1/projects/{project_id}", json=update_data)

        assert response.status_code == 400


class TestProjectDelete:
    """Test DELETE /api/v1/projects/{id} endpoint"""

    def test_delete_project_success(self, client, setup_test_data):
        """Should soft delete project (set is_active=False)"""
        # Create project
        project_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "project_code": "PROJ-DEL",
            "project_name": "Delete Test"
        }
        create_response = client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["id"]

        # Delete project
        response = client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 204

        # Verify still exists but inactive
        get_response = client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    def test_delete_project_not_found(self, client):
        """Should return 404 for non-existent project"""
        response = client.delete("/api/v1/projects/99999")

        assert response.status_code == 404
