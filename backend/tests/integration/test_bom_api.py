"""
Integration tests for BOM API endpoints.

Test Coverage:
- POST /api/v1/bom: Create BOM header
- GET /api/v1/bom: List BOMs with pagination and filters
- GET /api/v1/bom/{id}: Get BOM by ID
- GET /api/v1/bom/{id}/tree: Get BOM tree explosion
- PUT /api/v1/bom/{id}: Update BOM
- DELETE /api/v1/bom/{id}: Soft delete BOM
- POST /api/v1/bom/{id}/lines: Add BOM line
- PUT /api/v1/bom/{id}/lines/{line_id}: Update BOM line
- DELETE /api/v1/bom/{id}/lines/{line_id}: Delete BOM line
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
from app.models.material import Material, MaterialCategory, UnitOfMeasure
from app.models.bom import BOMHeader, BOMLine, BOMType


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bom.db"
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
    """Create test organization, plant, materials, and UoM for BOM tests"""
    # Create organization
    org = Organization(
        org_code="ORG001",
        org_name="Test Manufacturing Co",
        is_active=True
    )
    db_session.add(org)
    db_session.flush()

    # Create plant
    plant = Plant(
        organization_id=org.id,
        plant_code="PLT001",
        plant_name="Main Factory",
        location="Test City",
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
    category_fg = MaterialCategory(
        category_code="FG",
        category_name="Finished Goods",
        is_active=True
    )
    category_rm = MaterialCategory(
        category_code="RM",
        category_name="Raw Materials",
        is_active=True
    )
    db_session.add(category_fg)
    db_session.add(category_rm)
    db_session.flush()

    # Create finished good material (Bicycle)
    material_fg = Material(
        organization_id=org.id,
        plant_id=plant.id,
        material_number="MAT-FG-001",
        material_name="Bicycle",
        material_category_id=category_fg.id,
        base_unit_of_measure_id=uom.id,
        is_active=True
    )
    db_session.add(material_fg)
    db_session.flush()

    # Create component materials (Frame, Wheel)
    material_frame = Material(
        organization_id=org.id,
        plant_id=plant.id,
        material_number="MAT-COMP-001",
        material_name="Frame",
        material_category_id=category_rm.id,
        base_unit_of_measure_id=uom.id,
        is_active=True
    )
    material_wheel = Material(
        organization_id=org.id,
        plant_id=plant.id,
        material_number="MAT-COMP-002",
        material_name="Wheel",
        material_category_id=category_rm.id,
        base_unit_of_measure_id=uom.id,
        is_active=True
    )
    db_session.add(material_frame)
    db_session.add(material_wheel)
    db_session.flush()

    # Create sub-component materials (Steel Tube, Rim)
    material_steel = Material(
        organization_id=org.id,
        plant_id=plant.id,
        material_number="MAT-RM-001",
        material_name="Steel Tube",
        material_category_id=category_rm.id,
        base_unit_of_measure_id=uom.id,
        is_active=True
    )
    material_rim = Material(
        organization_id=org.id,
        plant_id=plant.id,
        material_number="MAT-RM-002",
        material_name="Rim",
        material_category_id=category_rm.id,
        base_unit_of_measure_id=uom.id,
        is_active=True
    )
    db_session.add(material_steel)
    db_session.add(material_rim)
    db_session.commit()

    return {
        "org_id": org.id,
        "plant_id": plant.id,
        "uom_id": uom.id,
        "material_fg_id": material_fg.id,
        "material_frame_id": material_frame.id,
        "material_wheel_id": material_wheel.id,
        "material_steel_id": material_steel.id,
        "material_rim_id": material_rim.id
    }


class TestBOMCreation:
    """Test POST /api/v1/bom endpoint"""

    def test_create_bom_success_full(self, client, setup_test_data):
        """Should create BOM with all fields"""
        bom_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-001",
            "material_id": setup_test_data["material_fg_id"],
            "bom_version": 1,
            "bom_name": "Bicycle BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "effective_start_date": "2025-01-01",
            "effective_end_date": "2025-12-31",
            "is_active": True,
            "created_by_user_id": 1
        }

        response = client.post("/api/v1/bom", json=bom_data)

        assert response.status_code == 201
        data = response.json()
        assert data["bom_number"] == "BOM-001"
        assert data["bom_name"] == "Bicycle BOM"
        assert data["bom_type"] == "PRODUCTION"
        assert data["base_quantity"] == 1.0
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_bom_minimal(self, client, setup_test_data):
        """Should create BOM with minimal required fields"""
        bom_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-MIN",
            "material_id": setup_test_data["material_fg_id"],
            "bom_name": "Minimal BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "created_by_user_id": 1
        }

        response = client.post("/api/v1/bom", json=bom_data)

        assert response.status_code == 201
        data = response.json()
        assert data["bom_version"] == 1  # Default
        assert data["is_active"] is True  # Default

    def test_create_bom_duplicate_fails(self, client, setup_test_data):
        """Should fail when creating BOM with duplicate (org, plant, material, version)"""
        bom_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-001",
            "material_id": setup_test_data["material_fg_id"],
            "bom_version": 1,
            "bom_name": "First BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "created_by_user_id": 1
        }

        # Create first BOM
        response1 = client.post("/api/v1/bom", json=bom_data)
        assert response1.status_code == 201

        # Try to create duplicate (same org, plant, material, version)
        bom_data["bom_number"] = "BOM-002"  # Different number, but same material+version
        response2 = client.post("/api/v1/bom", json=bom_data)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_bom_different_version_succeeds(self, client, setup_test_data):
        """Should allow multiple BOMs for same material with different versions"""
        bom_data_v1 = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-001",
            "material_id": setup_test_data["material_fg_id"],
            "bom_version": 1,
            "bom_name": "Bicycle BOM v1",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "created_by_user_id": 1
        }
        response1 = client.post("/api/v1/bom", json=bom_data_v1)
        assert response1.status_code == 201

        # Create version 2
        bom_data_v2 = bom_data_v1.copy()
        bom_data_v2["bom_number"] = "BOM-002"
        bom_data_v2["bom_version"] = 2
        bom_data_v2["bom_name"] = "Bicycle BOM v2"
        response2 = client.post("/api/v1/bom", json=bom_data_v2)
        assert response2.status_code == 201


class TestBOMRetrieval:
    """Test GET /api/v1/bom/{id} endpoint"""

    def test_get_bom_success(self, client, setup_test_data):
        """Should retrieve BOM by ID with lines"""
        # Create BOM
        bom_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-GET",
            "material_id": setup_test_data["material_fg_id"],
            "bom_name": "Get Test BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "created_by_user_id": 1
        }
        create_response = client.post("/api/v1/bom", json=bom_data)
        bom_id = create_response.json()["id"]

        # Get BOM
        response = client.get(f"/api/v1/bom/{bom_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bom_id
        assert data["bom_number"] == "BOM-GET"
        assert "bom_lines" in data
        assert isinstance(data["bom_lines"], list)

    def test_get_bom_not_found(self, client):
        """Should return 404 for non-existent BOM"""
        response = client.get("/api/v1/bom/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestBOMList:
    """Test GET /api/v1/bom endpoint"""

    def test_list_boms_empty(self, client, setup_test_data):
        """Should return empty list when no BOMs exist"""
        response = client.get("/api/v1/bom")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_boms_multiple(self, client, setup_test_data):
        """Should list multiple BOMs"""
        # Create multiple BOMs
        for i in range(3):
            bom_data = {
                "organization_id": setup_test_data["org_id"],
                "plant_id": setup_test_data["plant_id"],
                "bom_number": f"BOM-{i:03d}",
                "material_id": setup_test_data["material_fg_id"],
                "bom_version": i + 1,
                "bom_name": f"BOM {i}",
                "bom_type": "PRODUCTION",
                "base_quantity": 1.0,
                "unit_of_measure_id": setup_test_data["uom_id"],
                "created_by_user_id": 1
            }
            client.post("/api/v1/bom", json=bom_data)

        response = client.get("/api/v1/bom")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_list_boms_filter_by_material(self, client, setup_test_data):
        """Should filter BOMs by material_id"""
        # Create BOMs for different materials
        bom1_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-FG",
            "material_id": setup_test_data["material_fg_id"],
            "bom_name": "FG BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "created_by_user_id": 1
        }
        bom2_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-FRAME",
            "material_id": setup_test_data["material_frame_id"],
            "bom_name": "Frame BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "created_by_user_id": 1
        }
        client.post("/api/v1/bom", json=bom1_data)
        client.post("/api/v1/bom", json=bom2_data)

        # Filter by FG material
        response = client.get(f"/api/v1/bom?material_id={setup_test_data['material_fg_id']}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["material_id"] == setup_test_data["material_fg_id"]

    def test_list_boms_filter_by_active(self, client, setup_test_data, db_session):
        """Should filter BOMs by is_active status"""
        # Create active and inactive BOMs
        bom1_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-ACT",
            "material_id": setup_test_data["material_fg_id"],
            "bom_version": 1,
            "bom_name": "Active BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "is_active": True,
            "created_by_user_id": 1
        }
        bom2_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-INACT",
            "material_id": setup_test_data["material_fg_id"],
            "bom_version": 2,
            "bom_name": "Inactive BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "is_active": False,
            "created_by_user_id": 1
        }
        client.post("/api/v1/bom", json=bom1_data)
        client.post("/api/v1/bom", json=bom2_data)

        # Filter by active
        response = client.get("/api/v1/bom?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["is_active"] is True

    def test_list_boms_pagination(self, client, setup_test_data):
        """Should paginate BOM list"""
        # Create 15 BOMs (different versions of same material)
        for i in range(15):
            bom_data = {
                "organization_id": setup_test_data["org_id"],
                "plant_id": setup_test_data["plant_id"],
                "bom_number": f"BOM-{i:03d}",
                "material_id": setup_test_data["material_fg_id"],
                "bom_version": i + 1,
                "bom_name": f"BOM {i}",
                "bom_type": "PRODUCTION",
                "base_quantity": 1.0,
                "unit_of_measure_id": setup_test_data["uom_id"],
                "created_by_user_id": 1
            }
            client.post("/api/v1/bom", json=bom_data)

        # Get first page (page_size=10)
        response1 = client.get("/api/v1/bom?page=1&page_size=10")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 10
        assert data1["total"] == 15
        assert data1["page"] == 1

        # Get second page
        response2 = client.get("/api/v1/bom?page=2&page_size=10")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 5
        assert data2["total"] == 15
        assert data2["page"] == 2


class TestBOMUpdate:
    """Test PUT /api/v1/bom/{id} endpoint"""

    def test_update_bom_success(self, client, setup_test_data):
        """Should update BOM fields"""
        # Create BOM
        bom_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-UPD",
            "material_id": setup_test_data["material_fg_id"],
            "bom_name": "Original Name",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "created_by_user_id": 1
        }
        create_response = client.post("/api/v1/bom", json=bom_data)
        bom_id = create_response.json()["id"]

        # Update BOM
        update_data = {
            "bom_name": "Updated Name",
            "is_active": False
        }
        response = client.put(f"/api/v1/bom/{bom_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["bom_name"] == "Updated Name"
        assert data["is_active"] is False
        assert data["bom_number"] == "BOM-UPD"  # Unchanged

    def test_update_bom_not_found(self, client):
        """Should return 404 for non-existent BOM"""
        update_data = {"bom_name": "New Name"}
        response = client.put("/api/v1/bom/99999", json=update_data)

        assert response.status_code == 404


class TestBOMDelete:
    """Test DELETE /api/v1/bom/{id} endpoint"""

    def test_delete_bom_success(self, client, setup_test_data):
        """Should soft delete BOM (set is_active=False)"""
        # Create BOM
        bom_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-DEL",
            "material_id": setup_test_data["material_fg_id"],
            "bom_name": "Delete Test",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "created_by_user_id": 1
        }
        create_response = client.post("/api/v1/bom", json=bom_data)
        bom_id = create_response.json()["id"]

        # Delete BOM
        response = client.delete(f"/api/v1/bom/{bom_id}")
        assert response.status_code == 204

        # Verify still exists but inactive
        get_response = client.get(f"/api/v1/bom/{bom_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    def test_delete_bom_not_found(self, client):
        """Should return 404 for non-existent BOM"""
        response = client.delete("/api/v1/bom/99999")

        assert response.status_code == 404


class TestBOMLines:
    """Test BOM line endpoints"""

    def test_add_bom_line_success(self, client, setup_test_data):
        """Should add component to BOM"""
        # Create BOM
        bom_data = {
            "organization_id": setup_test_data["org_id"],
            "plant_id": setup_test_data["plant_id"],
            "bom_number": "BOM-LINE",
            "material_id": setup_test_data["material_fg_id"],
            "bom_name": "Line Test BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "created_by_user_id": 1
        }
        create_response = client.post("/api/v1/bom", json=bom_data)
        bom_id = create_response.json()["id"]

        # Add line (Frame component)
        line_data = {
            "bom_header_id": bom_id,
            "line_number": 10,
            "component_material_id": setup_test_data["material_frame_id"],
            "quantity": 1.0,
            "unit_of_measure_id": setup_test_data["uom_id"],
            "scrap_factor": 5.0
        }
        response = client.post(f"/api/v1/bom/{bom_id}/lines", json=line_data)

        assert response.status_code == 201
        data = response.json()
        assert data["bom_header_id"] == bom_id
        assert data["line_number"] == 10
        assert data["component_material_id"] == setup_test_data["material_frame_id"]
        assert data["quantity"] == 1.0
        assert data["scrap_factor"] == 5.0

    def test_update_bom_line_success(self, client, setup_test_data, db_session):
        """Should update BOM line quantity"""
        # Create BOM with line
        bom = BOMHeader(
            organization_id=setup_test_data["org_id"],
            plant_id=setup_test_data["plant_id"],
            bom_number="BOM-LINEUPD",
            material_id=setup_test_data["material_fg_id"],
            bom_version=1,
            bom_name="Line Update Test",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            created_by_user_id=1
        )
        db_session.add(bom)
        db_session.flush()

        line = BOMLine(
            bom_header_id=bom.id,
            line_number=10,
            component_material_id=setup_test_data["material_frame_id"],
            quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            scrap_factor=0.0
        )
        db_session.add(line)
        db_session.commit()

        # Update line
        update_data = {
            "quantity": 2.0,
            "scrap_factor": 10.0
        }
        response = client.put(f"/api/v1/bom/{bom.id}/lines/{line.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 2.0
        assert data["scrap_factor"] == 10.0

    def test_delete_bom_line_success(self, client, setup_test_data, db_session):
        """Should delete BOM line"""
        # Create BOM with line
        bom = BOMHeader(
            organization_id=setup_test_data["org_id"],
            plant_id=setup_test_data["plant_id"],
            bom_number="BOM-LINEDEL",
            material_id=setup_test_data["material_fg_id"],
            bom_version=1,
            bom_name="Line Delete Test",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            created_by_user_id=1
        )
        db_session.add(bom)
        db_session.flush()

        line = BOMLine(
            bom_header_id=bom.id,
            line_number=10,
            component_material_id=setup_test_data["material_frame_id"],
            quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            scrap_factor=0.0
        )
        db_session.add(line)
        db_session.commit()

        # Delete line
        response = client.delete(f"/api/v1/bom/{bom.id}/lines/{line.id}")
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/v1/bom/{bom.id}")
        assert get_response.status_code == 200
        assert len(get_response.json()["bom_lines"]) == 0


class TestBOMTreeExplosion:
    """Test GET /api/v1/bom/{id}/tree endpoint - multi-level BOM explosion"""

    def test_get_bom_tree_single_level(self, client, setup_test_data, db_session):
        """Should return BOM tree with 1 level (Bicycle -> Frame, Wheel)"""
        # Create Bicycle BOM (top level)
        bom_bicycle = BOMHeader(
            organization_id=setup_test_data["org_id"],
            plant_id=setup_test_data["plant_id"],
            bom_number="BOM-BICYCLE",
            material_id=setup_test_data["material_fg_id"],
            bom_version=1,
            bom_name="Bicycle BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            is_active=True,
            created_by_user_id=1
        )
        db_session.add(bom_bicycle)
        db_session.flush()

        # Add components (Frame, Wheel)
        line_frame = BOMLine(
            bom_header_id=bom_bicycle.id,
            line_number=10,
            component_material_id=setup_test_data["material_frame_id"],
            quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            scrap_factor=0.0
        )
        line_wheel = BOMLine(
            bom_header_id=bom_bicycle.id,
            line_number=20,
            component_material_id=setup_test_data["material_wheel_id"],
            quantity=2.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            scrap_factor=0.0
        )
        db_session.add(line_frame)
        db_session.add(line_wheel)
        db_session.commit()

        # Get BOM tree
        response = client.get(f"/api/v1/bom/{bom_bicycle.id}/tree")

        assert response.status_code == 200
        tree = response.json()
        assert tree["material_id"] == setup_test_data["material_fg_id"]
        assert tree["bom_id"] == bom_bicycle.id
        assert len(tree["components"]) == 2

        # Verify Frame component
        frame_comp = next(c for c in tree["components"] if c["component_material_id"] == setup_test_data["material_frame_id"])
        assert frame_comp["quantity"] == 1.0
        assert frame_comp["level"] == 1

        # Verify Wheel component
        wheel_comp = next(c for c in tree["components"] if c["component_material_id"] == setup_test_data["material_wheel_id"])
        assert wheel_comp["quantity"] == 2.0
        assert wheel_comp["level"] == 1

    def test_get_bom_tree_multi_level(self, client, setup_test_data, db_session):
        """Should return multi-level BOM tree (Bicycle -> Frame -> Steel Tube)"""
        # Create Bicycle BOM (Level 0)
        bom_bicycle = BOMHeader(
            organization_id=setup_test_data["org_id"],
            plant_id=setup_test_data["plant_id"],
            bom_number="BOM-BICYCLE",
            material_id=setup_test_data["material_fg_id"],
            bom_version=1,
            bom_name="Bicycle BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            is_active=True,
            created_by_user_id=1
        )
        db_session.add(bom_bicycle)
        db_session.flush()

        # Add Frame component (Level 1)
        line_frame = BOMLine(
            bom_header_id=bom_bicycle.id,
            line_number=10,
            component_material_id=setup_test_data["material_frame_id"],
            quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            scrap_factor=5.0
        )
        db_session.add(line_frame)
        db_session.flush()

        # Create Frame BOM (Level 1 -> Level 2)
        bom_frame = BOMHeader(
            organization_id=setup_test_data["org_id"],
            plant_id=setup_test_data["plant_id"],
            bom_number="BOM-FRAME",
            material_id=setup_test_data["material_frame_id"],
            bom_version=1,
            bom_name="Frame BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            is_active=True,
            created_by_user_id=1
        )
        db_session.add(bom_frame)
        db_session.flush()

        # Add Steel Tube component (Level 2)
        line_steel = BOMLine(
            bom_header_id=bom_frame.id,
            line_number=10,
            component_material_id=setup_test_data["material_steel_id"],
            quantity=3.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            scrap_factor=0.0
        )
        db_session.add(line_steel)
        db_session.commit()

        # Get BOM tree
        response = client.get(f"/api/v1/bom/{bom_bicycle.id}/tree")

        assert response.status_code == 200
        tree = response.json()

        # Verify top level
        assert tree["material_id"] == setup_test_data["material_fg_id"]
        assert len(tree["components"]) == 1

        # Verify Frame component (Level 1)
        frame_comp = tree["components"][0]
        assert frame_comp["component_material_id"] == setup_test_data["material_frame_id"]
        assert frame_comp["quantity"] == 1.0
        assert frame_comp["scrap_factor"] == 5.0
        assert frame_comp["level"] == 1

        # Verify Frame has sub-components
        assert "components" in frame_comp
        assert len(frame_comp["components"]) == 1

        # Verify Steel Tube component (Level 2)
        steel_comp = frame_comp["components"][0]
        assert steel_comp["component_material_id"] == setup_test_data["material_steel_id"]
        assert steel_comp["quantity"] == 3.0
        assert steel_comp["level"] == 2

    def test_get_bom_tree_respects_max_levels(self, client, setup_test_data, db_session):
        """Should respect max_levels parameter to prevent infinite recursion"""
        # Create 3-level BOM structure
        # Level 0: Bicycle
        bom_bicycle = BOMHeader(
            organization_id=setup_test_data["org_id"],
            plant_id=setup_test_data["plant_id"],
            bom_number="BOM-BICYCLE",
            material_id=setup_test_data["material_fg_id"],
            bom_version=1,
            bom_name="Bicycle BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=setup_test_data["uom_id"],
            is_active=True,
            created_by_user_id=1
        )
        db_session.add(bom_bicycle)
        db_session.flush()

        # Get tree with max_levels=1 (only show direct components)
        response = client.get(f"/api/v1/bom/{bom_bicycle.id}/tree?max_levels=1")

        assert response.status_code == 200
        tree = response.json()
        # Should only show level 1, no deeper recursion
        assert tree["material_id"] == setup_test_data["material_fg_id"]

    def test_get_bom_tree_not_found(self, client):
        """Should return 404 for non-existent BOM"""
        response = client.get("/api/v1/bom/99999/tree")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
