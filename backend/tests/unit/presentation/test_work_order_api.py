"""
Unit tests for Work Order API endpoints.
Phase 3 Component 5: Work Order API

Tests cover:
- POST /work-orders/: Create work order
- GET /work-orders/{id}: Get work order by ID
- GET /work-orders/: List work orders with pagination and filters
- PUT /work-orders/{id}: Update work order
- DELETE /work-orders/{id}: Cancel work order (soft delete)
- POST /work-orders/{id}/release: Release work order
- POST /work-orders/{id}/start: Start production
- POST /work-orders/{id}/complete: Complete work order
- POST /work-orders/{id}/operations: Add operation
- POST /work-orders/{id}/materials: Add material consumption
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.work_order import WorkOrder, WorkOrderOperation, WorkOrderMaterial, WorkCenter
from app.models.work_order import OrderType, OrderStatus, OperationStatus, WorkCenterType
from app.models.material import Material, UnitOfMeasure, MaterialCategory, ProcurementType, MRPType, DimensionType


class TestWorkOrderAPICreate:
    """Tests for POST /api/v1/work-orders/"""

    def test_create_work_order_success(self, client: TestClient, db: Session, auth_headers: dict):
        """Test successful work order creation"""
        # Setup: Create material, category, UOM
        category = MaterialCategory(
            organization_id=1,
            category_code="FG001",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT001",
            material_name="Test Product",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP,
            safety_stock=10.0,
            reorder_point=20.0,
            lot_size=50.0,
            lead_time_days=7
        )
        db.add(material)
        db.commit()

        # Request data
        request_data = {
            "material_id": material.id,
            "order_type": "PRODUCTION",
            "planned_quantity": 100.0,
            "start_date_planned": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_date_planned": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "priority": 5
        }

        # Execute
        response = client.post("/api/v1/work-orders/", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["material_id"] == material.id
        assert data["order_type"] == "PRODUCTION"
        assert data["order_status"] == "PLANNED"
        assert data["planned_quantity"] == 100.0
        assert data["actual_quantity"] == 0.0
        assert data["priority"] == 5
        assert "work_order_number" in data
        assert "id" in data

    def test_create_work_order_validation_error_negative_quantity(self, client: TestClient, auth_headers: dict):
        """Test validation error for negative planned quantity"""
        request_data = {
            "material_id": 1,
            "order_type": "PRODUCTION",
            "planned_quantity": -10.0,
            "priority": 5
        }

        response = client.post("/api/v1/work-orders/", json=request_data, headers=auth_headers)

        assert response.status_code == 400

    def test_create_work_order_validation_error_invalid_priority(self, client: TestClient, auth_headers: dict):
        """Test validation error for priority out of range (1-10)"""
        request_data = {
            "material_id": 1,
            "order_type": "PRODUCTION",
            "planned_quantity": 100.0,
            "priority": 15
        }

        response = client.post("/api/v1/work-orders/", json=request_data, headers=auth_headers)

        assert response.status_code == 400

    def test_create_work_order_material_not_found(self, client: TestClient, auth_headers: dict):
        """Test 404 when material doesn't exist"""
        request_data = {
            "material_id": 99999,
            "order_type": "PRODUCTION",
            "planned_quantity": 100.0,
            "priority": 5
        }

        response = client.post("/api/v1/work-orders/", json=request_data, headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_work_order_unauthorized(self, client: TestClient):
        """Test 401 when no auth token provided"""
        request_data = {
            "material_id": 1,
            "order_type": "PRODUCTION",
            "planned_quantity": 100.0,
            "priority": 5
        }

        response = client.post("/api/v1/work-orders/", json=request_data)

        assert response.status_code == 401


class TestWorkOrderAPIGet:
    """Tests for GET /api/v1/work-orders/{id}"""

    def test_get_work_order_success(self, client: TestClient, db: Session, auth_headers: dict):
        """Test successful retrieval of work order by ID"""
        # Setup: Create work order
        category = MaterialCategory(
            organization_id=1,
            category_code="FG002",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT002",
            material_name="Test Product 2",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO001",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        response = client.get(f"/api/v1/work-orders/{work_order.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == work_order.id
        assert data["work_order_number"] == "WO001"
        assert data["material_id"] == material.id
        assert data["order_status"] == "PLANNED"
        assert data["planned_quantity"] == 100.0

    def test_get_work_order_not_found(self, client: TestClient, auth_headers: dict):
        """Test 404 when work order doesn't exist"""
        response = client.get("/api/v1/work-orders/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_get_work_order_rls_isolation(self, client: TestClient, db: Session, auth_headers: dict):
        """Test RLS: Cannot access work order from different organization"""
        # Setup: Create work order for different organization
        category = MaterialCategory(
            organization_id=999,
            category_code="FG999",
            category_name="Other Org",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS2",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=999,
            plant_id=999,
            material_number="MAT999",
            material_name="Other Org Product",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=999,
            plant_id=999,
            work_order_number="WO999",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=999
        )
        db.add(work_order)
        db.commit()

        # Execute: Try to access with org_id=1 auth
        response = client.get(f"/api/v1/work-orders/{work_order.id}", headers=auth_headers)

        # Assert: Should not find (RLS filtering)
        assert response.status_code == 404


class TestWorkOrderAPIList:
    """Tests for GET /api/v1/work-orders/"""

    def test_list_work_orders_pagination(self, client: TestClient, db: Session, auth_headers: dict):
        """Test pagination works correctly"""
        # Setup: Create multiple work orders
        category = MaterialCategory(
            organization_id=1,
            category_code="FG003",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS3",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT003",
            material_name="Test Product 3",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        for i in range(5):
            wo = WorkOrder(
                organization_id=1,
                plant_id=1,
                work_order_number=f"WO00{i+10}",
                material_id=material.id,
                order_type=OrderType.PRODUCTION,
                order_status=OrderStatus.PLANNED,
                planned_quantity=100.0,
                actual_quantity=0.0,
                priority=5,
                created_by_user_id=1
            )
            db.add(wo)
        db.commit()

        # Execute: Get page 1 with page_size=2
        response = client.get("/api/v1/work-orders/?page=1&page_size=2", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["total"] >= 5
        assert data["total_pages"] >= 3

    def test_list_work_orders_filter_by_status(self, client: TestClient, db: Session, auth_headers: dict):
        """Test filtering by order status"""
        # Setup: Create work orders with different statuses
        category = MaterialCategory(
            organization_id=1,
            category_code="FG004",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS4",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT004",
            material_name="Test Product 4",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        # Create planned work order
        wo1 = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO020",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(wo1)

        # Create released work order
        wo2 = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO021",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.RELEASED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(wo2)
        db.commit()

        # Execute: Filter by RELEASED status
        response = client.get("/api/v1/work-orders/?status=RELEASED", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(item["order_status"] == "RELEASED" for item in data["items"])

    def test_list_work_orders_filter_by_material(self, client: TestClient, db: Session, auth_headers: dict):
        """Test filtering by material_id"""
        # Setup: Create materials and work orders
        category = MaterialCategory(
            organization_id=1,
            category_code="FG005",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS5",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material1 = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT005",
            material_name="Product A",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material1)
        db.flush()

        material2 = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT006",
            material_name="Product B",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material2)
        db.flush()

        wo1 = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO030",
            material_id=material1.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(wo1)

        wo2 = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO031",
            material_id=material2.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(wo2)
        db.commit()

        # Execute: Filter by material1
        response = client.get(f"/api/v1/work-orders/?material_id={material1.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(item["material_id"] == material1.id for item in data["items"])


class TestWorkOrderAPIUpdate:
    """Tests for PUT /api/v1/work-orders/{id}"""

    def test_update_work_order_success(self, client: TestClient, db: Session, auth_headers: dict):
        """Test successful work order update"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG006",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS6",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT007",
            material_name="Test Product 7",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO040",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute: Update priority and planned_quantity
        update_data = {
            "priority": 8,
            "planned_quantity": 150.0
        }
        response = client.put(f"/api/v1/work-orders/{work_order.id}", json=update_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == 8
        assert data["planned_quantity"] == 150.0

    def test_update_work_order_partial_update(self, client: TestClient, db: Session, auth_headers: dict):
        """Test partial update (only provided fields updated)"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG007",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS7",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT008",
            material_name="Test Product 8",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO041",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute: Update only priority
        update_data = {"priority": 9}
        response = client.put(f"/api/v1/work-orders/{work_order.id}", json=update_data, headers=auth_headers)

        # Assert: Priority updated, other fields unchanged
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == 9
        assert data["planned_quantity"] == 100.0  # Unchanged

    def test_update_work_order_not_found(self, client: TestClient, auth_headers: dict):
        """Test 404 when work order doesn't exist"""
        update_data = {"priority": 7}
        response = client.put("/api/v1/work-orders/99999", json=update_data, headers=auth_headers)

        assert response.status_code == 404

    def test_update_work_order_validation_error(self, client: TestClient, db: Session, auth_headers: dict):
        """Test validation error for invalid data"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG008",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS8",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT009",
            material_name="Test Product 9",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO042",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute: Invalid priority (out of range)
        update_data = {"priority": 20}
        response = client.put(f"/api/v1/work-orders/{work_order.id}", json=update_data, headers=auth_headers)

        # Assert
        assert response.status_code == 400


class TestWorkOrderAPIDelete:
    """Tests for DELETE /api/v1/work-orders/{id}"""

    def test_delete_work_order_success(self, client: TestClient, db: Session, auth_headers: dict):
        """Test successful work order cancellation (soft delete)"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG009",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS9",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT010",
            material_name="Test Product 10",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO050",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        response = client.delete(f"/api/v1/work-orders/{work_order.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 204

        # Verify status changed to CANCELLED
        db.refresh(work_order)
        assert work_order.order_status == OrderStatus.CANCELLED

    def test_delete_work_order_not_found(self, client: TestClient, auth_headers: dict):
        """Test 404 when work order doesn't exist"""
        response = client.delete("/api/v1/work-orders/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_work_order_already_cancelled(self, client: TestClient, db: Session, auth_headers: dict):
        """Test 409 conflict when trying to cancel already cancelled work order"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG010",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS10",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT011",
            material_name="Test Product 11",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO051",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.CANCELLED,  # Already cancelled
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        response = client.delete(f"/api/v1/work-orders/{work_order.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 409


class TestWorkOrderAPIRelease:
    """Tests for POST /api/v1/work-orders/{id}/release"""

    def test_release_work_order_success(self, client: TestClient, db: Session, auth_headers: dict):
        """Test successful work order release (PLANNED -> RELEASED)"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG011",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS11",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT012",
            material_name="Test Product 12",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO060",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        response = client.post(f"/api/v1/work-orders/{work_order.id}/release", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == "RELEASED"

    def test_release_work_order_invalid_state(self, client: TestClient, db: Session, auth_headers: dict):
        """Test 409 when trying to release from invalid state"""
        # Setup: Work order already IN_PROGRESS
        category = MaterialCategory(
            organization_id=1,
            category_code="FG012",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS12",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT013",
            material_name="Test Product 13",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO061",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.IN_PROGRESS,  # Not PLANNED
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        response = client.post(f"/api/v1/work-orders/{work_order.id}/release", headers=auth_headers)

        # Assert
        assert response.status_code == 409


class TestWorkOrderAPIStart:
    """Tests for POST /api/v1/work-orders/{id}/start"""

    def test_start_work_order_success(self, client: TestClient, db: Session, auth_headers: dict):
        """Test successful work order start (RELEASED -> IN_PROGRESS)"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG013",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS13",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT014",
            material_name="Test Product 14",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO070",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.RELEASED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        response = client.post(f"/api/v1/work-orders/{work_order.id}/start", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == "IN_PROGRESS"
        assert data["start_date_actual"] is not None

    def test_start_work_order_invalid_state(self, client: TestClient, db: Session, auth_headers: dict):
        """Test 409 when trying to start from invalid state"""
        # Setup: Work order is PLANNED (not RELEASED)
        category = MaterialCategory(
            organization_id=1,
            category_code="FG014",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS14",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT015",
            material_name="Test Product 15",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO071",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,  # Not RELEASED
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        response = client.post(f"/api/v1/work-orders/{work_order.id}/start", headers=auth_headers)

        # Assert
        assert response.status_code == 409


class TestWorkOrderAPIComplete:
    """Tests for POST /api/v1/work-orders/{id}/complete"""

    def test_complete_work_order_success(self, client: TestClient, db: Session, auth_headers: dict):
        """Test successful work order completion (IN_PROGRESS -> COMPLETED)"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG015",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS15",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT016",
            material_name="Test Product 16",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO080",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.IN_PROGRESS,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        response = client.post(f"/api/v1/work-orders/{work_order.id}/complete", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == "COMPLETED"
        assert data["end_date_actual"] is not None

    def test_complete_work_order_invalid_state(self, client: TestClient, db: Session, auth_headers: dict):
        """Test 409 when trying to complete from invalid state"""
        # Setup: Work order is PLANNED (not IN_PROGRESS)
        category = MaterialCategory(
            organization_id=1,
            category_code="FG016",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS16",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT017",
            material_name="Test Product 17",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO081",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,  # Not IN_PROGRESS
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        response = client.post(f"/api/v1/work-orders/{work_order.id}/complete", headers=auth_headers)

        # Assert
        assert response.status_code == 409


class TestWorkOrderAPIAddOperation:
    """Tests for POST /api/v1/work-orders/{id}/operations"""

    def test_add_operation_success(self, client: TestClient, db: Session, auth_headers: dict):
        """Test successfully adding operation to work order"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG017",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS17",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT018",
            material_name="Test Product 18",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_center = WorkCenter(
            organization_id=1,
            plant_id=1,
            work_center_code="WC001",
            work_center_name="Machine Center 1",
            work_center_type=WorkCenterType.MACHINE,
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=True
        )
        db.add(work_center)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO090",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        operation_data = {
            "operation_number": 10,
            "operation_name": "Cutting",
            "work_center_id": work_center.id,
            "setup_time_minutes": 30.0,
            "run_time_per_unit_minutes": 2.5
        }
        response = client.post(
            f"/api/v1/work-orders/{work_order.id}/operations",
            json=operation_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["operation_number"] == 10
        assert data["operation_name"] == "Cutting"
        assert data["work_center_id"] == work_center.id

    def test_add_operation_validation_error(self, client: TestClient, db: Session, auth_headers: dict):
        """Test validation error when adding invalid operation"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG018",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS18",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT019",
            material_name="Test Product 19",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO091",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute: Invalid operation_number (must be positive)
        operation_data = {
            "operation_number": -10,
            "operation_name": "Cutting",
            "work_center_id": 1,
            "setup_time_minutes": 30.0,
            "run_time_per_unit_minutes": 2.5
        }
        response = client.post(
            f"/api/v1/work-orders/{work_order.id}/operations",
            json=operation_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400


class TestWorkOrderAPIAddMaterial:
    """Tests for POST /api/v1/work-orders/{id}/materials"""

    def test_add_material_success(self, client: TestClient, db: Session, auth_headers: dict):
        """Test successfully adding material consumption to work order"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG019",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        raw_category = MaterialCategory(
            organization_id=1,
            category_code="RAW001",
            category_name="Raw Materials",
            is_active=True
        )
        db.add(raw_category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS19",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        finished_material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT020",
            material_name="Test Product 20",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(finished_material)
        db.flush()

        raw_material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT021",
            material_name="Raw Material Steel",
            material_category_id=raw_category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.REORDER
        )
        db.add(raw_material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO100",
            material_id=finished_material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute
        material_data = {
            "material_id": raw_material.id,
            "planned_quantity": 200.0,
            "unit_of_measure_id": uom.id,
            "backflush": False
        }
        response = client.post(
            f"/api/v1/work-orders/{work_order.id}/materials",
            json=material_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["material_id"] == raw_material.id
        assert data["planned_quantity"] == 200.0
        assert data["backflush"] == False

    def test_add_material_not_found(self, client: TestClient, db: Session, auth_headers: dict):
        """Test 404 when material doesn't exist"""
        # Setup
        category = MaterialCategory(
            organization_id=1,
            category_code="FG020",
            category_name="Finished Goods",
            is_active=True
        )
        db.add(category)
        db.flush()

        uom = UnitOfMeasure(
            uom_code="PCS20",
            uom_name="Pieces",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db.add(uom)
        db.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT022",
            material_name="Test Product 22",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db.add(material)
        db.flush()

        work_order = WorkOrder(
            organization_id=1,
            plant_id=1,
            work_order_number="WO101",
            material_id=material.id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db.add(work_order)
        db.commit()

        # Execute: Non-existent material_id
        material_data = {
            "material_id": 99999,
            "planned_quantity": 200.0,
            "unit_of_measure_id": uom.id,
            "backflush": False
        }
        response = client.post(
            f"/api/v1/work-orders/{work_order.id}/materials",
            json=material_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404
