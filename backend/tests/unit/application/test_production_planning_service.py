"""
Unit tests for ProductionPlanningService.
Phase 3: Production Planning Module - Component 3
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.application.services.production_planning_service import ProductionPlanningService
from app.models.work_order import WorkOrder, WorkOrderOperation, WorkOrderMaterial, OrderStatus, OrderType, OperationStatus
from app.models.bom import BOMHeader, BOMLine, BOMType
from app.models.material import Material, UnitOfMeasure, MaterialCategory, ProcurementType, MRPType, DimensionType
from app.models.work_order import WorkCenter, WorkCenterType


class TestProductionPlanningService:
    """Test suite for ProductionPlanningService"""

    @pytest.fixture
    def db_engine(self):
        """Create in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def db_session(self, db_engine):
        """Create a database session for testing"""
        Session = sessionmaker(bind=db_engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def setup_test_data(self, db_session):
        """Setup test data for production planning tests"""
        # Create UOM
        uom_ea = UnitOfMeasure(
            id=1,
            uom_code="EA",
            uom_name="Each",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        uom_kg = UnitOfMeasure(
            id=2,
            uom_code="KG",
            uom_name="Kilogram",
            dimension=DimensionType.MASS,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db_session.add_all([uom_ea, uom_kg])

        # Create category
        category = MaterialCategory(
            id=1,
            organization_id=1,
            category_code="PROD",
            category_name="Products",
            is_active=True
        )
        db_session.add(category)

        # Create materials
        finished_good = Material(
            id=1,
            organization_id=1,
            plant_id=1,
            material_number="FG001",
            material_name="Finished Product A",
            description="Main product",
            material_category_id=1,
            base_uom_id=1,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP,
            safety_stock=10.0,
            reorder_point=20.0,
            lot_size=1.0,
            lead_time_days=5,
            is_active=True
        )
        component_1 = Material(
            id=2,
            organization_id=1,
            plant_id=1,
            material_number="RM001",
            material_name="Raw Material 1",
            description="Component 1",
            material_category_id=1,
            base_uom_id=2,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.MRP,
            safety_stock=50.0,
            reorder_point=100.0,
            lot_size=1.0,
            lead_time_days=3,
            is_active=True
        )
        component_2 = Material(
            id=3,
            organization_id=1,
            plant_id=1,
            material_number="RM002",
            material_name="Raw Material 2",
            description="Component 2",
            material_category_id=1,
            base_uom_id=1,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.MRP,
            safety_stock=30.0,
            reorder_point=60.0,
            lot_size=1.0,
            lead_time_days=2,
            is_active=True
        )
        db_session.add_all([finished_good, component_1, component_2])

        # Create work centers
        wc_assembly = WorkCenter(
            id=1,
            organization_id=1,
            plant_id=1,
            work_center_code="ASSY-01",
            work_center_name="Assembly Line 1",
            work_center_type=WorkCenterType.ASSEMBLY,
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=True
        )
        wc_packaging = WorkCenter(
            id=2,
            organization_id=1,
            plant_id=1,
            work_center_code="PKG-01",
            work_center_name="Packaging Line 1",
            work_center_type=WorkCenterType.PACKAGING,
            capacity_per_hour=20.0,
            cost_per_hour=30.0,
            is_active=True
        )
        db_session.add_all([wc_assembly, wc_packaging])

        # Create BOM Header
        bom_header = BOMHeader(
            id=1,
            organization_id=1,
            plant_id=1,
            bom_number="BOM-FG001-V1",
            material_id=1,
            bom_version=1,
            bom_name="BOM for Product A",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=1,
            effective_date_from=datetime(2025, 1, 1),
            effective_date_to=datetime(2026, 12, 31),
            is_active=True,
            created_by_user_id=1
        )
        db_session.add(bom_header)

        # Create BOM Lines
        bom_line_1 = BOMLine(
            id=1,
            bom_header_id=1,
            line_number=10,
            component_material_id=2,
            quantity=2.2,  # 2.2 KG per unit
            unit_of_measure_id=2,
            scrap_factor=0.0,
            operation_number=10,
            is_phantom=False,
            backflush=True
        )
        bom_line_2 = BOMLine(
            id=2,
            bom_header_id=1,
            line_number=20,
            component_material_id=3,
            quantity=1.05,  # 1.05 EA per unit
            unit_of_measure_id=1,
            scrap_factor=5.0,  # 5% scrap
            operation_number=20,
            is_phantom=False,
            backflush=False
        )
        db_session.add_all([bom_line_1, bom_line_2])

        db_session.commit()

        return {
            'finished_good': finished_good,
            'component_1': component_1,
            'component_2': component_2,
            'bom_header': bom_header,
            'wc_assembly': wc_assembly,
            'wc_packaging': wc_packaging
        }

    def test_create_work_order_from_demand_success(self, db_session, setup_test_data):
        """Test creating work order from demand with active BOM"""
        service = ProductionPlanningService(db_session)

        due_date = datetime(2025, 12, 31)
        work_order = service.create_work_order_from_demand(
            material_id=1,
            quantity=100.0,
            due_date=due_date,
            organization_id=1,
            plant_id=1
        )

        assert work_order is not None
        assert work_order.material_id == 1
        assert work_order.planned_quantity == 100.0
        assert work_order.order_type == OrderType.PRODUCTION
        assert work_order.order_status == OrderStatus.PLANNED
        assert work_order.organization_id == 1
        assert work_order.plant_id == 1
        assert work_order.end_date_planned == due_date
        assert work_order.work_order_number is not None

    def test_create_work_order_from_demand_no_bom_error(self, db_session, setup_test_data):
        """Test error when material has no active BOM"""
        service = ProductionPlanningService(db_session)

        # Component material has no BOM
        with pytest.raises(ValueError, match="No active BOM found"):
            service.create_work_order_from_demand(
                material_id=2,
                quantity=100.0,
                due_date=datetime(2025, 12, 31),
                organization_id=1,
                plant_id=1
            )

    def test_create_work_order_from_demand_invalid_quantity(self, db_session, setup_test_data):
        """Test validation of quantity > 0"""
        service = ProductionPlanningService(db_session)

        with pytest.raises(ValueError, match="Quantity must be positive"):
            service.create_work_order_from_demand(
                material_id=1,
                quantity=0.0,
                due_date=datetime(2025, 12, 31),
                organization_id=1,
                plant_id=1
            )

    def test_calculate_material_requirements_single_level(self, db_session, setup_test_data):
        """Test material requirements calculation for single-level BOM"""
        service = ProductionPlanningService(db_session)

        # First create work order
        work_order = service.create_work_order_from_demand(
            material_id=1,
            quantity=100.0,
            due_date=datetime(2025, 12, 31),
            organization_id=1,
            plant_id=1
        )

        # Calculate material requirements
        requirements = service.calculate_material_requirements(work_order.id)

        assert requirements is not None
        assert len(requirements) == 2

        # Component 1: 2.2 KG per unit * 100 units = 220 KG
        assert 2 in requirements
        assert abs(requirements[2]['required_quantity'] - 220.0) < 0.01
        assert requirements[2]['unit_of_measure_id'] == 2

        # Component 2: 1.05 EA per unit * 100 units * 1.05 (scrap) = 110.25 EA
        assert 3 in requirements
        assert abs(requirements[3]['required_quantity'] - 110.25) < 0.01
        assert requirements[3]['unit_of_measure_id'] == 1

    def test_generate_operations_from_bom(self, db_session, setup_test_data):
        """Test generating work order operations from BOM routing"""
        service = ProductionPlanningService(db_session)

        # Create work order
        work_order = service.create_work_order_from_demand(
            material_id=1,
            quantity=100.0,
            due_date=datetime(2025, 12, 31),
            organization_id=1,
            plant_id=1
        )

        # Generate operations
        operations = service.generate_operations_from_bom(work_order.id, 1)

        assert operations is not None
        assert len(operations) == 2

        # Operation 10 - Assembly
        assert operations[0].operation_number == 10
        assert operations[0].work_order_id == work_order.id
        assert operations[0].status == OperationStatus.PENDING

        # Operation 20 - Packaging
        assert operations[1].operation_number == 20
        assert operations[1].work_order_id == work_order.id
        assert operations[1].status == OperationStatus.PENDING

    def test_check_capacity_feasibility_sufficient_capacity(self, db_session, setup_test_data):
        """Test capacity check when work center has sufficient capacity"""
        service = ProductionPlanningService(db_session)

        # Create work order with operations
        work_order = service.create_work_order_from_demand(
            material_id=1,
            quantity=100.0,
            due_date=datetime(2025, 12, 31),
            organization_id=1,
            plant_id=1
        )

        # Add operation with reasonable hours
        operation = WorkOrderOperation(
            organization_id=1,
            plant_id=1,
            work_order_id=work_order.id,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=1,
            setup_time_minutes=60.0,  # 1 hour setup
            run_time_per_unit_minutes=3.0,  # 3 minutes per unit, 100 units = 300 min = 5 hours
            status=OperationStatus.PENDING
        )
        db_session.add(operation)
        db_session.commit()

        # Check capacity feasibility
        result = service.check_capacity_feasibility(work_order.id)

        assert result is not None
        assert result['feasible'] is True
        assert result['capacity_utilization'] < 100.0

    def test_check_capacity_feasibility_overloaded(self, db_session, setup_test_data):
        """Test capacity check when work center is overloaded"""
        service = ProductionPlanningService(db_session)

        # Create work order
        work_order = service.create_work_order_from_demand(
            material_id=1,
            quantity=100.0,
            due_date=datetime.now() + timedelta(days=1),  # Short deadline
            organization_id=1,
            plant_id=1
        )

        # Add operation with excessive hours
        operation = WorkOrderOperation(
            organization_id=1,
            plant_id=1,
            work_order_id=work_order.id,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=1,
            setup_time_minutes=480.0,  # 8 hours setup
            run_time_per_unit_minutes=60.0,  # 60 minutes per unit, 100 units = 6000 min = 100 hours
            status=OperationStatus.PENDING
        )
        db_session.add(operation)
        db_session.commit()

        # Check capacity feasibility (should be overloaded)
        result = service.check_capacity_feasibility(work_order.id)

        assert result is not None
        assert result['feasible'] is False
        assert result['capacity_utilization'] > 100.0
        assert 'bottleneck_work_center' in result
        assert 'earliest_completion_date' in result
