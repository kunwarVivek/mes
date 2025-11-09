"""
Integration tests for Metrics API Router.

Tests dashboard metrics endpoint with:
- JWT authentication
- RLS context enforcement
- Aggregated counts (not limited by pagination)
- Large datasets (>100 items)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.models.material import Material, ProcurementType, MRPType
from app.models.work_order import WorkOrder, OrderStatus, OrderType
from app.models.ncr import NCR, NCRStatus, DefectType
from app.infrastructure.security.jwt_handler import JWTHandler


jwt_handler = JWTHandler()


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create a test client with test database."""
    from app.main import app

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_test_token(organization_id: int = 1, plant_id: int = 1, user_id: int = 1) -> str:
    """Create a test JWT token with org/plant context."""
    payload = {
        "sub": str(user_id),
        "type": "access",
        "organization_id": organization_id,
        "plant_id": plant_id,
    }
    return jwt_handler.create_access_token(payload)


class TestDashboardMetricsEndpoint:
    """Test dashboard metrics endpoint."""

    def test_get_dashboard_metrics_returns_aggregated_counts(self, client, test_db):
        """Test that metrics endpoint returns accurate aggregated counts."""
        # Create test token
        token = create_test_token(organization_id=1, plant_id=1)

        # Create 5 materials
        for i in range(5):
            material = Material(
                organization_id=1,
                plant_id=1,
                material_number=f"MAT-{i:03d}",
                description=f"Test Material {i}",
                procurement_type=ProcurementType.BUY,
                mrp_type=MRPType.MRP,
                base_unit_of_measure="EA",
            )
            test_db.add(material)

        # Create 8 work orders with different statuses
        for i in range(8):
            wo = WorkOrder(
                organization_id=1,
                plant_id=1,
                order_number=f"WO-{i:04d}",
                order_type=OrderType.PRODUCTION,
                order_status=OrderStatus.PLANNED if i < 3 else (
                    OrderStatus.RELEASED if i < 5 else OrderStatus.IN_PROGRESS
                ),
                planned_quantity=100,
            )
            test_db.add(wo)

        # Create 12 NCRs with different statuses
        for i in range(12):
            ncr = NCR(
                organization_id=1,
                plant_id=1,
                ncr_number=f"NCR-{i:04d}",
                defect_type=DefectType.DIMENSIONAL,
                defect_description=f"Defect {i}",
                quantity_defective=1,
                status=NCRStatus.OPEN if i < 4 else (
                    NCRStatus.IN_REVIEW if i < 8 else NCRStatus.RESOLVED
                ),
                reported_by_user_id=1,
            )
            test_db.add(ncr)

        test_db.commit()

        # Call metrics endpoint
        response = client.get(
            "/api/v1/metrics/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify aggregated counts
        assert data["materials_count"] == 5
        assert data["work_orders_count"] == 8
        assert data["ncrs_count"] == 12

        # Verify status breakdown
        assert data["work_orders_by_status"]["PLANNED"] == 3
        assert data["work_orders_by_status"]["RELEASED"] == 2
        assert data["work_orders_by_status"]["IN_PROGRESS"] == 3
        assert data["work_orders_by_status"]["COMPLETED"] == 0
        assert data["work_orders_by_status"]["CANCELLED"] == 0

        assert data["ncrs_by_status"]["OPEN"] == 4
        assert data["ncrs_by_status"]["IN_REVIEW"] == 4
        assert data["ncrs_by_status"]["RESOLVED"] == 4
        assert data["ncrs_by_status"]["CLOSED"] == 0

    def test_get_dashboard_metrics_with_large_dataset(self, client, test_db):
        """Test that metrics endpoint handles datasets > 100 items correctly."""
        # Create test token
        token = create_test_token(organization_id=2, plant_id=2)

        # Create 150 materials (exceeds pagination limit of 100)
        for i in range(150):
            material = Material(
                organization_id=2,
                plant_id=2,
                material_number=f"MAT-LARGE-{i:04d}",
                description=f"Large Dataset Material {i}",
                procurement_type=ProcurementType.BUY,
                mrp_type=MRPType.MRP,
                base_unit_of_measure="EA",
            )
            test_db.add(material)

        # Create 120 work orders
        for i in range(120):
            wo = WorkOrder(
                organization_id=2,
                plant_id=2,
                order_number=f"WO-LARGE-{i:05d}",
                order_type=OrderType.PRODUCTION,
                order_status=OrderStatus.PLANNED,
                planned_quantity=100,
            )
            test_db.add(wo)

        # Create 200 NCRs
        for i in range(200):
            ncr = NCR(
                organization_id=2,
                plant_id=2,
                ncr_number=f"NCR-LARGE-{i:05d}",
                defect_type=DefectType.DIMENSIONAL,
                defect_description=f"Large Dataset Defect {i}",
                quantity_defective=1,
                status=NCRStatus.OPEN,
                reported_by_user_id=1,
            )
            test_db.add(ncr)

        test_db.commit()

        # Call metrics endpoint
        response = client.get(
            "/api/v1/metrics/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify counts exceed pagination limit
        assert data["materials_count"] == 150, "Should count all materials, not just first 100"
        assert data["work_orders_count"] == 120, "Should count all work orders, not just first 100"
        assert data["ncrs_count"] == 200, "Should count all NCRs, not just first 100"

    def test_get_dashboard_metrics_respects_rls(self, client, test_db):
        """Test that metrics endpoint respects RLS (organization_id, plant_id)."""
        # Create data for org 1
        for i in range(10):
            material = Material(
                organization_id=1,
                plant_id=1,
                material_number=f"ORG1-MAT-{i:03d}",
                description=f"Org 1 Material {i}",
                procurement_type=ProcurementType.BUY,
                mrp_type=MRPType.MRP,
                base_unit_of_measure="EA",
            )
            test_db.add(material)

        # Create data for org 2
        for i in range(15):
            material = Material(
                organization_id=2,
                plant_id=2,
                material_number=f"ORG2-MAT-{i:03d}",
                description=f"Org 2 Material {i}",
                procurement_type=ProcurementType.BUY,
                mrp_type=MRPType.MRP,
                base_unit_of_measure="EA",
            )
            test_db.add(material)

        test_db.commit()

        # Token for org 1
        token_org1 = create_test_token(organization_id=1, plant_id=1)
        response_org1 = client.get(
            "/api/v1/metrics/dashboard",
            headers={"Authorization": f"Bearer {token_org1}"}
        )

        assert response_org1.status_code == 200
        data_org1 = response_org1.json()
        assert data_org1["materials_count"] == 10, "Should only count org 1 materials"

        # Token for org 2
        token_org2 = create_test_token(organization_id=2, plant_id=2)
        response_org2 = client.get(
            "/api/v1/metrics/dashboard",
            headers={"Authorization": f"Bearer {token_org2}"}
        )

        assert response_org2.status_code == 200
        data_org2 = response_org2.json()
        assert data_org2["materials_count"] == 15, "Should only count org 2 materials"

    def test_get_dashboard_metrics_requires_authentication(self, client):
        """Test that metrics endpoint requires JWT authentication."""
        response = client.get("/api/v1/metrics/dashboard")

        assert response.status_code == 403, "Should require authentication"

    def test_get_dashboard_metrics_returns_zero_for_empty_data(self, client, test_db):
        """Test that metrics endpoint returns zero counts for empty datasets."""
        # Create test token for org with no data
        token = create_test_token(organization_id=999, plant_id=999)

        response = client.get(
            "/api/v1/metrics/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all counts are zero
        assert data["materials_count"] == 0
        assert data["work_orders_count"] == 0
        assert data["ncrs_count"] == 0

        # Verify status breakdowns are all zero
        for status in ["PLANNED", "RELEASED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]:
            assert data["work_orders_by_status"][status] == 0

        for status in ["OPEN", "IN_REVIEW", "RESOLVED", "CLOSED"]:
            assert data["ncrs_by_status"][status] == 0
