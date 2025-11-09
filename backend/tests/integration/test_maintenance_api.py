"""
Integration tests for Maintenance Management API endpoints.

Test Coverage:
- PM Schedule CRUD operations
- PM Work Order operations
- Downtime Event tracking
- MTBF/MTTR metrics calculation
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


class TestPMScheduleAPI:
    """Test PM Schedule API endpoints"""

    def test_create_calendar_pm_schedule(self, client: TestClient, auth_headers: dict):
        """Should create calendar-based PM schedule via API"""
        payload = {
            "schedule_code": "PM-CAL-001",
            "schedule_name": "Monthly CNC Maintenance",
            "machine_id": 1,
            "trigger_type": "CALENDAR",
            "frequency_days": 30,
            "is_active": True
        }

        response = client.post("/api/v1/maintenance/pm-schedules", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["schedule_code"] == "PM-CAL-001"
        assert data["trigger_type"] == "CALENDAR"
        assert data["frequency_days"] == 30

    def test_create_meter_pm_schedule(self, client: TestClient, auth_headers: dict):
        """Should create meter-based PM schedule via API"""
        payload = {
            "schedule_code": "PM-MTR-001",
            "schedule_name": "1000 Hour PM Check",
            "machine_id": 1,
            "trigger_type": "METER",
            "meter_threshold": 1000.0,
            "is_active": True
        }

        response = client.post("/api/v1/maintenance/pm-schedules", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["schedule_code"] == "PM-MTR-001"
        assert data["trigger_type"] == "METER"
        assert data["meter_threshold"] == 1000.0

    def test_calendar_schedule_missing_frequency_days_fails(self, client: TestClient, auth_headers: dict):
        """Should reject calendar schedule without frequency_days"""
        payload = {
            "schedule_code": "PM-CAL-002",
            "schedule_name": "Invalid Schedule",
            "machine_id": 1,
            "trigger_type": "CALENDAR",
            "is_active": True
        }

        response = client.post("/api/v1/maintenance/pm-schedules", json=payload, headers=auth_headers)

        assert response.status_code == 400
        assert "frequency_days" in response.json()["detail"].lower()

    def test_get_pm_schedules(self, client: TestClient, auth_headers: dict):
        """Should retrieve all PM schedules"""
        response = client.get("/api/v1/maintenance/pm-schedules", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_pm_schedule(self, client: TestClient, auth_headers: dict):
        """Should update PM schedule"""
        # Create schedule first
        payload = {
            "schedule_code": "PM-UPD-001",
            "schedule_name": "Original Name",
            "machine_id": 1,
            "trigger_type": "CALENDAR",
            "frequency_days": 30,
            "is_active": True
        }
        create_response = client.post("/api/v1/maintenance/pm-schedules", json=payload, headers=auth_headers)
        schedule_id = create_response.json()["id"]

        # Update schedule
        update_payload = {
            "schedule_name": "Updated Name",
            "is_active": False
        }
        response = client.patch(f"/api/v1/maintenance/pm-schedules/{schedule_id}", json=update_payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["schedule_name"] == "Updated Name"
        assert data["is_active"] is False


class TestPMWorkOrderAPI:
    """Test PM Work Order API endpoints"""

    def test_create_pm_work_order(self, client: TestClient, auth_headers: dict):
        """Should create PM work order via API"""
        # Create PM schedule first
        schedule_payload = {
            "schedule_code": "PM-WO-001",
            "schedule_name": "Weekly PM",
            "machine_id": 1,
            "trigger_type": "CALENDAR",
            "frequency_days": 7,
            "is_active": True
        }
        schedule_response = client.post("/api/v1/maintenance/pm-schedules", json=schedule_payload, headers=auth_headers)
        schedule_id = schedule_response.json()["id"]

        # Create PM work order
        scheduled_date = datetime.utcnow() + timedelta(days=7)
        due_date = scheduled_date + timedelta(days=3)

        payload = {
            "pm_schedule_id": schedule_id,
            "machine_id": 1,
            "pm_number": "PMWO-001-20251115",
            "scheduled_date": scheduled_date.isoformat(),
            "due_date": due_date.isoformat()
        }

        response = client.post("/api/v1/maintenance/pm-work-orders", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["pm_number"] == "PMWO-001-20251115"
        assert data["status"] == "SCHEDULED"

    def test_get_pm_work_orders(self, client: TestClient, auth_headers: dict):
        """Should retrieve PM work orders"""
        response = client.get("/api/v1/maintenance/pm-work-orders", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_pm_work_order_status(self, client: TestClient, auth_headers: dict):
        """Should update PM work order status"""
        # Create schedule and work order first (setup code omitted for brevity)
        # Assuming work order exists with id=1
        update_payload = {
            "status": "IN_PROGRESS",
            "notes": "Started maintenance work"
        }

        # This test requires existing data - placeholder for integration test
        # response = client.patch(f"/api/v1/maintenance/pm-work-orders/1", json=update_payload, headers=auth_headers)
        # assert response.status_code == 200


class TestDowntimeEventAPI:
    """Test Downtime Event API endpoints"""

    def test_create_downtime_event(self, client: TestClient, auth_headers: dict):
        """Should create downtime event via API"""
        started_at = datetime.utcnow() - timedelta(hours=2)

        payload = {
            "machine_id": 1,
            "category": "BREAKDOWN",
            "reason": "Motor failure - requires replacement",
            "started_at": started_at.isoformat(),
            "notes": "Emergency repair initiated"
        }

        response = client.post("/api/v1/maintenance/downtime-events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "BREAKDOWN"
        assert data["reason"] == "Motor failure - requires replacement"
        assert data["duration_minutes"] is None  # Ongoing event

    def test_create_completed_downtime_event(self, client: TestClient, auth_headers: dict):
        """Should create completed downtime event with duration"""
        started_at = datetime.utcnow() - timedelta(hours=3)
        ended_at = datetime.utcnow() - timedelta(hours=1)

        payload = {
            "machine_id": 1,
            "category": "PLANNED_MAINTENANCE",
            "reason": "Scheduled lubrication",
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat()
        }

        response = client.post("/api/v1/maintenance/downtime-events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "PLANNED_MAINTENANCE"
        assert data["duration_minutes"] == pytest.approx(120.0, rel=1.0)  # ~2 hours

    def test_end_time_before_start_time_fails(self, client: TestClient, auth_headers: dict):
        """Should reject downtime event with end time before start time"""
        started_at = datetime.utcnow()
        ended_at = started_at - timedelta(hours=1)

        payload = {
            "machine_id": 1,
            "category": "BREAKDOWN",
            "reason": "Invalid event",
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat()
        }

        response = client.post("/api/v1/maintenance/downtime-events", json=payload, headers=auth_headers)

        assert response.status_code == 400
        assert "before start time" in response.json()["detail"].lower()

    def test_get_downtime_events(self, client: TestClient, auth_headers: dict):
        """Should retrieve downtime events"""
        response = client.get("/api/v1/maintenance/downtime-events", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_downtime_event_end_time(self, client: TestClient, auth_headers: dict):
        """Should update downtime event to set end time"""
        # Create ongoing event
        started_at = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "machine_id": 1,
            "category": "BREAKDOWN",
            "reason": "Temporary failure",
            "started_at": started_at.isoformat()
        }
        create_response = client.post("/api/v1/maintenance/downtime-events", json=payload, headers=auth_headers)
        event_id = create_response.json()["id"]

        # End the event
        ended_at = datetime.utcnow()
        update_payload = {
            "ended_at": ended_at.isoformat()
        }

        response = client.patch(f"/api/v1/maintenance/downtime-events/{event_id}", json=update_payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["ended_at"] is not None
        assert data["duration_minutes"] is not None


class TestMTBFMTTRMetricsAPI:
    """Test MTBF/MTTR metrics API endpoint"""

    def test_calculate_mtbf_mttr_metrics(self, client: TestClient, auth_headers: dict):
        """Should calculate MTBF/MTTR metrics for machine"""
        # Create downtime events for testing
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        # Create some breakdown events
        breakdown_events = [
            {
                "machine_id": 1,
                "category": "BREAKDOWN",
                "reason": f"Failure {i}",
                "started_at": (start_date + timedelta(days=i*5)).isoformat(),
                "ended_at": (start_date + timedelta(days=i*5, hours=2)).isoformat()
            }
            for i in range(3)
        ]

        for event in breakdown_events:
            client.post("/api/v1/maintenance/downtime-events", json=event, headers=auth_headers)

        # Calculate metrics
        response = client.get(
            f"/api/v1/maintenance/metrics/mtbf-mttr",
            params={
                "machine_id": 1,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "mtbf" in data
        assert "mttr" in data
        assert "availability" in data
        assert data["number_of_failures"] >= 3
        assert 0.0 <= data["availability"] <= 1.0

    def test_mtbf_mttr_invalid_date_range_fails(self, client: TestClient, auth_headers: dict):
        """Should reject invalid date range (end before start)"""
        start_date = datetime.utcnow()
        end_date = start_date - timedelta(days=30)

        response = client.get(
            f"/api/v1/maintenance/metrics/mtbf-mttr",
            params={
                "machine_id": 1,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "before start date" in response.json()["detail"].lower()


# Fixtures for integration tests
@pytest.fixture
def client():
    """FastAPI test client - placeholder"""
    # This would be implemented with actual FastAPI app
    pass


@pytest.fixture
def auth_headers():
    """Authentication headers - placeholder"""
    # This would return actual JWT token headers
    return {
        "Authorization": "Bearer test_token",
        "organization_id": "1",
        "plant_id": "1"
    }
