"""
Integration tests for Department API endpoints.

Test Coverage:
- POST /api/v1/departments: Create department
- GET /api/v1/departments: List departments with pagination and plant_id filter
- GET /api/v1/departments/{id}: Get department by ID
- PUT /api/v1/departments/{id}: Update department
- DELETE /api/v1/departments/{id}: Soft delete department
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_departments.db"
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


@pytest.fixture(scope="function")
def sample_plant(db_session):
    """Create a sample plant for testing departments"""
    from app.models.organization import Organization
    from app.models.plant import Plant

    # Create organization first
    org = Organization(
        org_code="TEST001",
        org_name="Test Organization",
        is_active=True
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # Create plant
    plant = Plant(
        organization_id=org.id,
        plant_code="PLT001",
        plant_name="Test Plant",
        is_active=True
    )
    db_session.add(plant)
    db_session.commit()
    db_session.refresh(plant)

    return plant


class TestDepartmentCreation:
    """Test POST /api/v1/departments endpoint"""

    def test_create_department_success(self, client, db_session, sample_plant):
        """Should create department with valid data"""
        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "description": "Handles all production activities",
            "is_active": True
        }

        response = client.post("/api/v1/departments", json=dept_data)

        assert response.status_code == 201
        data = response.json()
        assert data["dept_code"] == "PROD"
        assert data["dept_name"] == "Production Department"
        assert data["description"] == "Handles all production activities"
        assert data["plant_id"] == sample_plant.id
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_department_without_description(self, client, db_session, sample_plant):
        """Should create department without description"""
        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "QC",
            "dept_name": "Quality Control",
            "is_active": True
        }

        response = client.post("/api/v1/departments", json=dept_data)

        assert response.status_code == 201
        data = response.json()
        assert data["dept_code"] == "QC"
        assert data["description"] is None

    def test_create_department_duplicate_code_in_same_plant_fails(self, client, db_session, sample_plant):
        """Should fail when creating department with duplicate dept_code within same plant"""
        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "is_active": True
        }

        # Create first department
        response1 = client.post("/api/v1/departments", json=dept_data)
        assert response1.status_code == 201

        # Try to create duplicate in same plant
        dept_data["dept_name"] = "Another Production Department"
        response2 = client.post("/api/v1/departments", json=dept_data)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_department_same_code_different_plants_succeeds(self, client, db_session, sample_plant):
        """Should allow same dept_code in different plants"""
        from app.models.plant import Plant

        # Create second plant
        plant2 = Plant(
            organization_id=sample_plant.organization_id,
            plant_code="PLT002",
            plant_name="Second Plant",
            is_active=True
        )
        db_session.add(plant2)
        db_session.commit()
        db_session.refresh(plant2)

        # Create department in first plant
        dept_data1 = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department - Plant 1",
            "is_active": True
        }
        response1 = client.post("/api/v1/departments", json=dept_data1)
        assert response1.status_code == 201

        # Create department with same code in second plant
        dept_data2 = {
            "plant_id": plant2.id,
            "dept_code": "PROD",
            "dept_name": "Production Department - Plant 2",
            "is_active": True
        }
        response2 = client.post("/api/v1/departments", json=dept_data2)
        assert response2.status_code == 201

    def test_create_department_invalid_plant_id_fails(self, client, db_session):
        """Should fail when plant_id does not exist"""
        dept_data = {
            "plant_id": 999,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "is_active": True
        }

        response = client.post("/api/v1/departments", json=dept_data)

        assert response.status_code == 400
        assert "plant" in response.json()["detail"].lower()


class TestDepartmentRetrieval:
    """Test GET /api/v1/departments endpoints"""

    def test_get_departments_list(self, client, db_session, sample_plant):
        """Should return paginated list of departments"""
        # Create test departments
        for i in range(5):
            dept_data = {
                "plant_id": sample_plant.id,
                "dept_code": f"DEPT{i:02d}",
                "dept_name": f"Department {i}",
                "is_active": True
            }
            client.post("/api/v1/departments", json=dept_data)

        # Get list
        response = client.get("/api/v1/departments")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_get_departments_filter_by_plant_id(self, client, db_session, sample_plant):
        """Should filter departments by plant_id"""
        from app.models.plant import Plant

        # Create second plant
        plant2 = Plant(
            organization_id=sample_plant.organization_id,
            plant_code="PLT002",
            plant_name="Second Plant",
            is_active=True
        )
        db_session.add(plant2)
        db_session.commit()
        db_session.refresh(plant2)

        # Create departments in first plant
        for i in range(3):
            dept_data = {
                "plant_id": sample_plant.id,
                "dept_code": f"DEPT{i:02d}",
                "dept_name": f"Plant 1 Department {i}",
                "is_active": True
            }
            client.post("/api/v1/departments", json=dept_data)

        # Create departments in second plant
        for i in range(2):
            dept_data = {
                "plant_id": plant2.id,
                "dept_code": f"DEPT{i:02d}",
                "dept_name": f"Plant 2 Department {i}",
                "is_active": True
            }
            client.post("/api/v1/departments", json=dept_data)

        # Filter by first plant
        response = client.get(f"/api/v1/departments?plant_id={sample_plant.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(item["plant_id"] == sample_plant.id for item in data["items"])

        # Filter by second plant
        response = client.get(f"/api/v1/departments?plant_id={plant2.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["plant_id"] == plant2.id for item in data["items"])

    def test_get_departments_with_pagination(self, client, db_session, sample_plant):
        """Should return paginated list with custom page size"""
        # Create 10 departments
        for i in range(10):
            dept_data = {
                "plant_id": sample_plant.id,
                "dept_code": f"DEPT{i:02d}",
                "dept_name": f"Department {i}",
                "is_active": True
            }
            client.post("/api/v1/departments", json=dept_data)

        # Get first page
        response = client.get("/api/v1/departments?page=1&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total_pages"] == 2

        # Get second page
        response = client.get("/api/v1/departments?page=2&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 2

    def test_get_department_by_id(self, client, db_session, sample_plant):
        """Should return department by ID"""
        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "description": "Production activities",
            "is_active": True
        }

        # Create department
        create_response = client.post("/api/v1/departments", json=dept_data)
        dept_id = create_response.json()["id"]

        # Get by ID
        response = client.get(f"/api/v1/departments/{dept_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == dept_id
        assert data["dept_code"] == "PROD"
        assert data["dept_name"] == "Production Department"

    def test_get_department_by_invalid_id(self, client, db_session):
        """Should return 404 for non-existent department"""
        response = client.get("/api/v1/departments/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDepartmentUpdate:
    """Test PUT /api/v1/departments/{id} endpoint"""

    def test_update_department_success(self, client, db_session, sample_plant):
        """Should update department with valid data"""
        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Original Name",
            "description": "Original description",
            "is_active": True
        }

        # Create department
        create_response = client.post("/api/v1/departments", json=dept_data)
        dept_id = create_response.json()["id"]

        # Update department
        update_data = {
            "dept_name": "Updated Name",
            "description": "Updated description"
        }
        response = client.put(f"/api/v1/departments/{dept_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["dept_name"] == "Updated Name"
        assert data["description"] == "Updated description"
        assert data["dept_code"] == "PROD"  # Should not change

    def test_update_department_partial(self, client, db_session, sample_plant):
        """Should support partial updates"""
        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Original Name",
            "description": "Original description",
            "is_active": True
        }

        # Create department
        create_response = client.post("/api/v1/departments", json=dept_data)
        dept_id = create_response.json()["id"]

        # Update only dept_name
        update_data = {"dept_name": "Updated Name"}
        response = client.put(f"/api/v1/departments/{dept_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["dept_name"] == "Updated Name"
        assert data["description"] == "Original description"  # Should remain unchanged

    def test_update_department_deactivate(self, client, db_session, sample_plant):
        """Should deactivate department"""
        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "is_active": True
        }

        # Create department
        create_response = client.post("/api/v1/departments", json=dept_data)
        dept_id = create_response.json()["id"]

        # Deactivate
        update_data = {"is_active": False}
        response = client.put(f"/api/v1/departments/{dept_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_update_department_invalid_id(self, client, db_session):
        """Should return 404 for non-existent department"""
        update_data = {"dept_name": "Updated Name"}
        response = client.put("/api/v1/departments/999", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDepartmentDeletion:
    """Test DELETE /api/v1/departments/{id} endpoint"""

    def test_delete_department_success(self, client, db_session, sample_plant):
        """Should soft delete department"""
        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "is_active": True
        }

        # Create department
        create_response = client.post("/api/v1/departments", json=dept_data)
        dept_id = create_response.json()["id"]

        # Delete department
        response = client.delete(f"/api/v1/departments/{dept_id}")

        assert response.status_code == 204

        # Verify soft delete (is_active=False)
        get_response = client.get(f"/api/v1/departments/{dept_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    def test_delete_department_invalid_id(self, client, db_session):
        """Should return 404 for non-existent department"""
        response = client.delete("/api/v1/departments/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
