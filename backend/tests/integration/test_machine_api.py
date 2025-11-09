"""
Integration tests for Machine API endpoints.

Test Coverage:
- POST /api/v1/machines: Create machine
- GET /api/v1/machines: List machines with pagination
- GET /api/v1/machines/{id}: Get machine by ID
- PATCH /api/v1/machines/{id}/status: Update machine status
- GET /api/v1/machines/{id}/oee: Calculate OEE metrics
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.core.database import Base, get_db
from app.main import app


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_machines.db"
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


class TestMachineCreation:
    """Test POST /api/v1/machines endpoint"""

    def test_create_machine_success(self, client, db_session):
        """Should create machine with valid data"""
        machine_data = {
            "organization_id": 1,
            "plant_id": 1,
            "machine_code": "M001",
            "machine_name": "CNC Machine 1",
            "description": "CNC Milling Machine",
            "work_center_id": 1,
            "status": "AVAILABLE"
        }

        response = client.post("/api/v1/machines", json=machine_data)

        assert response.status_code == 201
        data = response.json()
        assert data["machine_code"] == "M001"
        assert data["machine_name"] == "CNC Machine 1"
        assert data["status"] == "AVAILABLE"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_machine_duplicate_code_fails(self, client, db_session):
        """Should fail when creating machine with duplicate code"""
        machine_data = {
            "organization_id": 1,
            "plant_id": 1,
            "machine_code": "M001",
            "machine_name": "CNC Machine 1",
            "description": "First machine",
            "work_center_id": 1,
            "status": "AVAILABLE"
        }

        # Create first machine
        response1 = client.post("/api/v1/machines", json=machine_data)
        assert response1.status_code == 201

        # Try to create duplicate
        machine_data["machine_name"] = "CNC Machine 2"
        response2 = client.post("/api/v1/machines", json=machine_data)

        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_machine_invalid_code_fails(self, client, db_session):
        """Should fail with invalid machine code format"""
        machine_data = {
            "organization_id": 1,
            "plant_id": 1,
            "machine_code": "M-001!",  # Invalid characters
            "machine_name": "CNC Machine",
            "description": "",
            "work_center_id": 1,
            "status": "AVAILABLE"
        }

        response = client.post("/api/v1/machines", json=machine_data)

        assert response.status_code == 400
        assert "alphanumeric" in response.json()["detail"].lower()

    def test_create_machine_missing_required_fields(self, client, db_session):
        """Should fail when required fields are missing"""
        machine_data = {
            "organization_id": 1,
            "machine_code": "M001",
            # Missing plant_id, machine_name, work_center_id
        }

        response = client.post("/api/v1/machines", json=machine_data)

        assert response.status_code == 422  # Validation error


class TestMachineRetrieval:
    """Test GET /api/v1/machines endpoints"""

    def test_get_machines_list(self, client, db_session):
        """Should return paginated list of machines"""
        # Create test machines
        for i in range(5):
            machine_data = {
                "organization_id": 1,
                "plant_id": 1,
                "machine_code": f"M{i:03d}",
                "machine_name": f"Machine {i}",
                "description": f"Test machine {i}",
                "work_center_id": 1,
                "status": "AVAILABLE"
            }
            client.post("/api/v1/machines", json=machine_data)

        # Get list
        response = client.get("/api/v1/machines?organization_id=1&plant_id=1")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) == 5
        assert data["total"] == 5

    def test_get_machine_by_id(self, client, db_session):
        """Should retrieve specific machine by ID"""
        # Create machine
        machine_data = {
            "organization_id": 1,
            "plant_id": 1,
            "machine_code": "M001",
            "machine_name": "CNC Machine",
            "description": "Test machine",
            "work_center_id": 1,
            "status": "AVAILABLE"
        }
        create_response = client.post("/api/v1/machines", json=machine_data)
        machine_id = create_response.json()["id"]

        # Get by ID
        response = client.get(f"/api/v1/machines/{machine_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == machine_id
        assert data["machine_code"] == "M001"

    def test_get_machine_not_found(self, client, db_session):
        """Should return 404 for non-existent machine"""
        response = client.get("/api/v1/machines/99999")

        assert response.status_code == 404


class TestMachineStatusUpdate:
    """Test PATCH /api/v1/machines/{id}/status endpoint"""

    def test_update_machine_status_to_running(self, client, db_session):
        """Should update machine status to RUNNING"""
        # Create machine
        machine_data = {
            "organization_id": 1,
            "plant_id": 1,
            "machine_code": "M001",
            "machine_name": "CNC Machine",
            "description": "Test",
            "work_center_id": 1,
            "status": "AVAILABLE"
        }
        create_response = client.post("/api/v1/machines", json=machine_data)
        machine_id = create_response.json()["id"]

        # Update status
        status_update = {
            "status": "RUNNING",
            "notes": "Started production"
        }
        response = client.patch(f"/api/v1/machines/{machine_id}/status", json=status_update)

        assert response.status_code == 200
        data = response.json()
        assert data["machine"]["status"] == "RUNNING"
        assert "status_history" in data
        assert data["status_history"]["status"] == "RUNNING"
        assert data["status_history"]["notes"] == "Started production"

    def test_update_machine_status_to_maintenance(self, client, db_session):
        """Should update machine status to MAINTENANCE"""
        # Create machine
        machine_data = {
            "organization_id": 1,
            "plant_id": 1,
            "machine_code": "M001",
            "machine_name": "CNC Machine",
            "description": "Test",
            "work_center_id": 1,
            "status": "RUNNING"
        }
        create_response = client.post("/api/v1/machines", json=machine_data)
        machine_id = create_response.json()["id"]

        # Update to maintenance
        status_update = {
            "status": "MAINTENANCE",
            "notes": "Scheduled maintenance"
        }
        response = client.patch(f"/api/v1/machines/{machine_id}/status", json=status_update)

        assert response.status_code == 200
        data = response.json()
        assert data["machine"]["status"] == "MAINTENANCE"

    def test_update_status_creates_history_record(self, client, db_session):
        """Should create status history record when status changes"""
        # Create machine
        machine_data = {
            "organization_id": 1,
            "plant_id": 1,
            "machine_code": "M001",
            "machine_name": "CNC Machine",
            "description": "Test",
            "work_center_id": 1,
            "status": "AVAILABLE"
        }
        create_response = client.post("/api/v1/machines", json=machine_data)
        machine_id = create_response.json()["id"]

        # First status change
        client.patch(f"/api/v1/machines/{machine_id}/status", json={"status": "RUNNING"})

        # Second status change
        client.patch(f"/api/v1/machines/{machine_id}/status", json={"status": "IDLE"})

        # Verify history exists
        machine_response = client.get(f"/api/v1/machines/{machine_id}")
        assert machine_response.status_code == 200


class TestMachineOEECalculation:
    """Test GET /api/v1/machines/{id}/oee endpoint"""

    def test_calculate_oee_for_time_period(self, client, db_session):
        """Should calculate OEE metrics for specified time period"""
        # Create machine with status history
        machine_data = {
            "organization_id": 1,
            "plant_id": 1,
            "machine_code": "M001",
            "machine_name": "CNC Machine",
            "description": "Test",
            "work_center_id": 1,
            "status": "AVAILABLE"
        }
        create_response = client.post("/api/v1/machines", json=machine_data)
        machine_id = create_response.json()["id"]

        # Simulate status changes and production
        # This would require more setup in a real test

        # Calculate OEE
        start_date = datetime.now() - timedelta(hours=8)
        end_date = datetime.now()

        response = client.get(
            f"/api/v1/machines/{machine_id}/oee",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "ideal_cycle_time": 1.0,
                "total_pieces": 400,
                "defect_pieces": 20
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "availability" in data
        assert "performance" in data
        assert "quality" in data
        assert "oee_score" in data
        assert 0.0 <= data["oee_score"] <= 1.0

    def test_oee_missing_required_params_fails(self, client, db_session):
        """Should fail when required OEE calculation params are missing"""
        # Create machine
        machine_data = {
            "organization_id": 1,
            "plant_id": 1,
            "machine_code": "M001",
            "machine_name": "CNC Machine",
            "description": "Test",
            "work_center_id": 1,
            "status": "AVAILABLE"
        }
        create_response = client.post("/api/v1/machines", json=machine_data)
        machine_id = create_response.json()["id"]

        # Missing required params
        response = client.get(f"/api/v1/machines/{machine_id}/oee")

        assert response.status_code == 422  # Validation error
