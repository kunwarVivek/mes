"""
Unit tests for MRPService.
Phase 3: Production Planning Module - Component 4 (MRP)
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.application.services.mrp_service import MRPService
from app.domain.services.lot_sizing_service import LotSizingService
from app.domain.entities.mrp_run import MRPRunDomain
from app.domain.entities.planned_order import PlannedOrderDomain
from app.models.material import Material, UnitOfMeasure, MaterialCategory, ProcurementType, MRPType, DimensionType
from app.models.inventory import Inventory, StorageLocation, LocationType
from app.models.work_order import WorkOrder, WorkOrderMaterial, OrderStatus, OrderType
from app.models.bom import BOMHeader, BOMLine, BOMType


class TestMRPService:
    """Test suite for MRPService"""

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
        """Setup test data for MRP tests"""
        # Create UOM
        uom_ea = UnitOfMeasure(
            id=1,
            uom_code="EA",
            uom_name="Each",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db_session.add(uom_ea)

        # Create Material Category
        category = MaterialCategory(
            id=1,
            organization_id=1,
            category_code="RM",
            category_name="Raw Materials",
            is_active=True
        )
        db_session.add(category)

        # Create Materials (Purchased)
        material_purchased = Material(
            id=1,
            organization_id=1,
            plant_id=1,
            material_number="MAT-001",
            material_name="Purchased Material A",
            material_category_id=1,
            base_uom_id=1,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.MRP,
            lead_time_days=7,
            safety_stock=50.0,
            reorder_point=100.0,
            lot_size=100.0,
            is_active=True
        )
        db_session.add(material_purchased)

        # Create Materials (Manufactured)
        material_manufactured = Material(
            id=2,
            organization_id=1,
            plant_id=1,
            material_number="MAT-002",
            material_name="Manufactured Material B",
            material_category_id=1,
            base_uom_id=1,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP,
            lead_time_days=14,
            safety_stock=20.0,
            reorder_point=50.0,
            lot_size=50.0,
            is_active=True
        )
        db_session.add(material_manufactured)

        # Create Material with no MRP
        material_no_mrp = Material(
            id=3,
            organization_id=1,
            plant_id=1,
            material_number="MAT-003",
            material_name="Non-MRP Material",
            material_category_id=1,
            base_uom_id=1,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.REORDER,
            lead_time_days=5,
            safety_stock=10.0,
            reorder_point=20.0,
            is_active=True
        )
        db_session.add(material_no_mrp)

        # Create Storage Location
        location = StorageLocation(
            id=1,
            organization_id=1,
            plant_id=1,
            location_code="WH-01",
            location_name="Main Warehouse",
            location_type=LocationType.WAREHOUSE,
            is_active=True
        )
        db_session.add(location)

        # Create Inventory
        inventory_purchased = Inventory(
            id=1,
            organization_id=1,
            plant_id=1,
            material_id=1,
            storage_location_id=1,
            batch_number="BATCH-001",
            quantity_on_hand=100.0,
            quantity_reserved=0.0,
            unit_of_measure_id=1
        )
        db_session.add(inventory_purchased)

        inventory_manufactured = Inventory(
            id=2,
            organization_id=1,
            plant_id=1,
            material_id=2,
            storage_location_id=1,
            batch_number="BATCH-002",
            quantity_on_hand=30.0,
            quantity_reserved=0.0,
            unit_of_measure_id=1
        )
        db_session.add(inventory_manufactured)

        db_session.commit()
        return {
            'uom_ea': uom_ea,
            'category': category,
            'material_purchased': material_purchased,
            'material_manufactured': material_manufactured,
            'material_no_mrp': material_no_mrp,
            'location': location,
            'inventory_purchased': inventory_purchased,
            'inventory_manufactured': inventory_manufactured
        }

    @pytest.fixture
    def mrp_service(self, db_session):
        """Create MRPService instance"""
        return MRPService(db_session)

    # ========== Test calculate_net_requirements ==========

    def test_calculate_net_requirements_surplus_inventory(self, mrp_service, setup_test_data, db_session):
        """RED: Test calculate_net_requirements when inventory is sufficient (no shortage)"""
        # Setup: Current inventory = 100, no work orders = 0 demand
        # Expected: No net requirements (surplus)
        material_id = setup_test_data['material_purchased'].id
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=90)

        result = mrp_service.calculate_net_requirements(material_id, start_date, end_date)

        assert result['gross_requirements'] == 0.0
        assert result['scheduled_receipts'] == 0.0
        assert result['on_hand'] == 100.0
        assert result['net_requirements'] == 0.0
        assert result['shortage_dates'] == []

    def test_calculate_net_requirements_shortage(self, mrp_service, setup_test_data, db_session):
        """RED: Test calculate_net_requirements when shortage exists"""
        # Setup: Current inventory = 100, work orders demand = 150
        # Expected: Net requirement = 50
        material = setup_test_data['material_purchased']
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=90)

        # Create work order requiring 150 units (shortage of 50)
        work_order = WorkOrder(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-001",
            material_id=2,  # Manufactured material
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=start_date + timedelta(days=30),
            end_date_planned=start_date + timedelta(days=45),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)

        # Work order requires purchased material as component
        wo_material = WorkOrderMaterial(
            id=1,
            work_order_id=1,
            material_id=material.id,  # Purchased material
            planned_quantity=150.0,
            actual_quantity=0.0,
            unit_of_measure_id=1
        )
        db_session.add(wo_material)
        db_session.commit()

        result = mrp_service.calculate_net_requirements(material.id, start_date, end_date)

        assert result['gross_requirements'] == 150.0
        assert result['scheduled_receipts'] == 0.0
        assert result['on_hand'] == 100.0
        assert result['net_requirements'] == 50.0
        assert len(result['shortage_dates']) == 1

    def test_calculate_net_requirements_zero_inventory(self, mrp_service, setup_test_data, db_session):
        """RED: Test calculate_net_requirements with zero inventory"""
        # Create material with zero inventory
        material = Material(
            id=10,
            organization_id=1,
            plant_id=1,
            material_number="MAT-ZERO",
            material_name="Zero Inventory Material",
            material_category_id=1,
            base_uom_id=1,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.MRP,
            lead_time_days=5,
            safety_stock=0.0,
            reorder_point=0.0,
            is_active=True
        )
        db_session.add(material)
        db_session.commit()

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=90)

        result = mrp_service.calculate_net_requirements(material.id, start_date, end_date)

        assert result['gross_requirements'] == 0.0
        assert result['scheduled_receipts'] == 0.0
        assert result['on_hand'] == 0.0
        assert result['net_requirements'] == 0.0

    # ========== Test generate_planned_orders ==========

    def test_generate_planned_orders_purchase(self, mrp_service, setup_test_data, db_session):
        """RED: Test generate_planned_orders for purchased material"""
        material = setup_test_data['material_purchased']
        net_requirements = 150.0
        need_date = datetime.utcnow() + timedelta(days=30)
        lead_time_days = material.lead_time_days

        planned_orders = mrp_service.generate_planned_orders(
            material_id=material.id,
            net_requirements=net_requirements,
            need_date=need_date,
            lead_time_days=lead_time_days
        )

        assert len(planned_orders) == 1
        order = planned_orders[0]
        assert order.material_id == material.id
        assert order.order_type == 'PURCHASE'
        assert order.planned_quantity == 200.0  # Rounded to lot size 100
        assert order.status == 'PLANNED'
        # Order date should be offset by lead time
        expected_order_date = need_date - timedelta(days=lead_time_days)
        assert (order.order_date - expected_order_date).days == 0

    def test_generate_planned_orders_manufacture(self, mrp_service, setup_test_data, db_session):
        """RED: Test generate_planned_orders for manufactured material"""
        material = setup_test_data['material_manufactured']
        net_requirements = 75.0
        need_date = datetime.utcnow() + timedelta(days=45)
        lead_time_days = material.lead_time_days

        planned_orders = mrp_service.generate_planned_orders(
            material_id=material.id,
            net_requirements=net_requirements,
            need_date=need_date,
            lead_time_days=lead_time_days
        )

        assert len(planned_orders) == 1
        order = planned_orders[0]
        assert order.material_id == material.id
        assert order.order_type == 'PRODUCTION'
        assert order.planned_quantity == 100.0  # Rounded to lot size 50
        assert order.status == 'PLANNED'

    # ========== Test run_mrp ==========

    def test_run_mrp_success_multiple_materials(self, mrp_service, setup_test_data, db_session):
        """RED: Test run_mrp processes multiple MRP materials"""
        organization_id = 1
        plant_id = 1
        planning_horizon_days = 90

        # Create work orders creating demand
        start_date = datetime.utcnow()
        work_order = WorkOrder(
            id=2,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-002",
            material_id=2,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=200.0,
            actual_quantity=0.0,
            start_date_planned=start_date + timedelta(days=30),
            end_date_planned=start_date + timedelta(days=45),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)

        # Work order materials
        wo_mat1 = WorkOrderMaterial(
            id=2,
            work_order_id=2,
            material_id=1,
            planned_quantity=300.0,
            actual_quantity=0.0,
            unit_of_measure_id=1
        )
        db_session.add(wo_mat1)
        db_session.commit()

        mrp_run = mrp_service.run_mrp(organization_id, plant_id, planning_horizon_days)

        assert mrp_run is not None
        assert mrp_run.organization_id == organization_id
        assert mrp_run.plant_id == plant_id
        assert mrp_run.status == 'COMPLETED'
        assert mrp_run.materials_processed >= 2  # At least 2 MRP materials
        assert mrp_run.planned_orders_created >= 1  # At least 1 planned order

    def test_run_mrp_no_mrp_materials(self, mrp_service, db_session):
        """RED: Test run_mrp when no MRP materials exist"""
        # Create organization with no MRP materials
        organization_id = 99
        plant_id = 99
        planning_horizon_days = 90

        mrp_run = mrp_service.run_mrp(organization_id, plant_id, planning_horizon_days)

        assert mrp_run is not None
        assert mrp_run.organization_id == organization_id
        assert mrp_run.plant_id == plant_id
        assert mrp_run.status == 'COMPLETED'
        assert mrp_run.materials_processed == 0
        assert mrp_run.planned_orders_created == 0

    # ========== Test explode_requirements ==========

    def test_explode_requirements_single_level_bom(self, mrp_service, setup_test_data, db_session):
        """RED: Test explode_requirements with single-level BOM"""
        # Create BOM
        start_date = datetime.utcnow()
        bom_header = BOMHeader(
            id=1,
            organization_id=1,
            plant_id=1,
            material_id=2,  # Manufactured material
            bom_number="BOM-001",
            bom_name="BOM for Manufactured Material B",
            bom_type=BOMType.PRODUCTION,
            bom_version=1,
            base_quantity=1.0,
            unit_of_measure_id=1,
            effective_date_from=start_date,
            effective_date_to=start_date + timedelta(days=365),
            is_active=True,
            created_by_user_id=1
        )
        db_session.add(bom_header)

        bom_line = BOMLine(
            id=1,
            bom_header_id=1,
            line_number=10,
            component_material_id=1,  # Purchased material
            quantity=2.0,
            unit_of_measure_id=1,
            scrap_factor=5.0,
            is_phantom=False
        )
        db_session.add(bom_line)

        # Create work order
        start_date = datetime.utcnow()
        work_order = WorkOrder(
            id=3,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-003",
            material_id=2,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=start_date + timedelta(days=10),
            end_date_planned=start_date + timedelta(days=20),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        requirements = mrp_service.explode_requirements(work_order.id)

        assert len(requirements) >= 1
        # Expected: 100 units * 2.0 qty * 1.05 scrap = 210 units of component
        req = requirements[0]
        assert req['material_id'] == 1
        assert req['quantity'] == 210.0
        assert req['parent_work_order_id'] == work_order.id


class TestLotSizingService:
    """Test suite for LotSizingService"""

    def test_lot_for_lot(self):
        """RED: Test LOT_FOR_LOT lot sizing rule"""
        service = LotSizingService()
        net_requirement = 137.0
        lot_sizing_rule = 'LOT_FOR_LOT'

        lot_size = service.calculate_lot_size(
            material_id=1,
            net_requirement=net_requirement,
            lot_sizing_rule=lot_sizing_rule
        )

        assert lot_size == 137.0  # Exactly what's needed

    def test_fixed_lot_size(self):
        """RED: Test FIXED_LOT_SIZE lot sizing rule"""
        service = LotSizingService()
        net_requirement = 150.0
        lot_sizing_rule = 'FIXED_LOT_SIZE'
        fixed_lot = 100.0

        lot_size = service.calculate_lot_size(
            material_id=1,
            net_requirement=net_requirement,
            lot_sizing_rule=lot_sizing_rule,
            fixed_lot_size=fixed_lot
        )

        # 150 / 100 = 1.5 → round up to 2 → 200
        assert lot_size == 200.0

    def test_eoq_lot_sizing(self):
        """RED: Test EOQ (Economic Order Quantity) lot sizing rule"""
        service = LotSizingService()
        net_requirement = 500.0
        lot_sizing_rule = 'EOQ'
        annual_demand = 12000.0
        ordering_cost = 50.0
        holding_cost_rate = 0.2
        unit_cost = 10.0

        lot_size = service.calculate_lot_size(
            material_id=1,
            net_requirement=net_requirement,
            lot_sizing_rule=lot_sizing_rule,
            annual_demand=annual_demand,
            ordering_cost=ordering_cost,
            holding_cost_rate=holding_cost_rate,
            unit_cost=unit_cost
        )

        # EOQ formula: sqrt((2 * D * S) / (H * C))
        # sqrt((2 * 12000 * 50) / (0.2 * 10)) = sqrt(1200000 / 2) = sqrt(600000) ≈ 775
        assert lot_size >= 700.0  # Approximately 775


class TestMRPRunEntity:
    """Test suite for MRPRunDomain entity"""

    def test_create_mrp_run(self):
        """RED: Test MRPRun entity creation"""
        mrp_run = MRPRunDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            run_number="MRP-2025-001",
            run_date=datetime.utcnow(),
            planning_horizon_start=datetime.utcnow(),
            planning_horizon_end=datetime.utcnow() + timedelta(days=90),
            materials_processed=0,
            planned_orders_created=0,
            total_shortage_qty=0.0,
            status='RUNNING'
        )

        assert mrp_run.organization_id == 1
        assert mrp_run.plant_id == 1
        assert mrp_run.status == 'RUNNING'
        assert mrp_run.materials_processed == 0
        assert mrp_run.planned_orders_created == 0

    def test_mrp_run_complete(self):
        """RED: Test MRPRun complete status transition"""
        mrp_run = MRPRunDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            run_number="MRP-2025-002",
            run_date=datetime.utcnow(),
            planning_horizon_start=datetime.utcnow(),
            planning_horizon_end=datetime.utcnow() + timedelta(days=90),
            materials_processed=0,
            planned_orders_created=0,
            total_shortage_qty=0.0,
            status='RUNNING'
        )

        mrp_run.complete(materials_processed=10, planned_orders_created=5, total_shortage_qty=500.0)

        assert mrp_run.status == 'COMPLETED'
        assert mrp_run.materials_processed == 10
        assert mrp_run.planned_orders_created == 5
        assert mrp_run.total_shortage_qty == 500.0
        assert mrp_run.completed_at is not None

    def test_mrp_run_fail(self):
        """RED: Test MRPRun fail status transition"""
        mrp_run = MRPRunDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            run_number="MRP-2025-003",
            run_date=datetime.utcnow(),
            planning_horizon_start=datetime.utcnow(),
            planning_horizon_end=datetime.utcnow() + timedelta(days=90),
            materials_processed=0,
            planned_orders_created=0,
            total_shortage_qty=0.0,
            status='RUNNING'
        )

        mrp_run.fail()

        assert mrp_run.status == 'FAILED'
        assert mrp_run.completed_at is not None


class TestPlannedOrderEntity:
    """Test suite for PlannedOrderDomain entity"""

    def test_create_planned_order(self):
        """RED: Test PlannedOrder entity creation"""
        need_date = datetime.utcnow() + timedelta(days=30)
        order_date = need_date - timedelta(days=7)

        planned_order = PlannedOrderDomain(
            id=None,
            mrp_run_id=1,
            material_id=1,
            order_type='PURCHASE',
            planned_quantity=100.0,
            unit_of_measure_id=1,
            need_date=need_date,
            order_date=order_date,
            source='MRP',
            status='PLANNED'
        )

        assert planned_order.material_id == 1
        assert planned_order.order_type == 'PURCHASE'
        assert planned_order.planned_quantity == 100.0
        assert planned_order.status == 'PLANNED'

    def test_planned_order_firm(self):
        """RED: Test PlannedOrder firm status transition"""
        need_date = datetime.utcnow() + timedelta(days=30)
        order_date = need_date - timedelta(days=7)

        planned_order = PlannedOrderDomain(
            id=None,
            mrp_run_id=1,
            material_id=1,
            order_type='PURCHASE',
            planned_quantity=100.0,
            unit_of_measure_id=1,
            need_date=need_date,
            order_date=order_date,
            source='MRP',
            status='PLANNED'
        )

        planned_order.firm()

        assert planned_order.status == 'FIRMED'

    def test_planned_order_convert_to_work_order(self):
        """RED: Test PlannedOrder conversion to work order"""
        need_date = datetime.utcnow() + timedelta(days=30)
        order_date = need_date - timedelta(days=14)

        planned_order = PlannedOrderDomain(
            id=None,
            mrp_run_id=1,
            material_id=2,
            order_type='PRODUCTION',
            planned_quantity=50.0,
            unit_of_measure_id=1,
            need_date=need_date,
            order_date=order_date,
            source='MRP',
            status='FIRMED'
        )

        planned_order.convert_to_work_order()

        assert planned_order.status == 'CONVERTED'
        assert planned_order.converted_to_order_id is not None
