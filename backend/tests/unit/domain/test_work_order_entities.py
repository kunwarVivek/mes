"""
Unit tests for Work Order domain entities.
Following TDD approach: RED -> GREEN -> REFACTOR
Phase 3: Production Planning Module
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.core.database import Base
from app.models.work_order import (
    WorkOrder,
    WorkOrderOperation,
    WorkCenter,
    WorkOrderMaterial,
    OrderType,
    OrderStatus,
    OperationStatus,
    WorkCenterType
)
from app.models.material import Material, MaterialCategory, UnitOfMeasure


@pytest.fixture
def db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a database session for testing"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_dependencies(db_session):
    """Setup common test dependencies: UOM, Category, Material, WorkCenter"""
    # Create UOM
    uom = UnitOfMeasure(
        uom_code="EA",
        uom_name="Each",
        dimension="QUANTITY",
        is_base_unit=True,
        conversion_factor=1.0
    )
    db_session.add(uom)

    # Create Category
    category = MaterialCategory(
        organization_id=1,
        category_code="FERT",
        category_name="Finished Goods",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()

    # Create Material (finished good)
    material = Material(
        organization_id=1,
        plant_id=101,
        material_number="FG001",
        material_name="Finished Product A",
        description="Test finished good",
        material_category_id=category.id,
        base_uom_id=uom.id,
        procurement_type="MANUFACTURE",
        mrp_type="MRP",
        safety_stock=100.0,
        reorder_point=50.0,
        lot_size=10.0,
        lead_time_days=5,
        is_active=True
    )
    db_session.add(material)

    # Create WorkCenter
    work_center = WorkCenter(
        organization_id=1,
        plant_id=101,
        work_center_code="WC001",
        work_center_name="Assembly Line 1",
        work_center_type=WorkCenterType.ASSEMBLY,
        capacity_per_hour=10.0,
        cost_per_hour=50.0,
        is_active=True
    )
    db_session.add(work_center)
    db_session.commit()

    return {
        'uom': uom,
        'category': category,
        'material': material,
        'work_center': work_center
    }


class TestWorkCenter:
    """Test WorkCenter entity"""

    def test_create_work_center(self, db_session):
        """Test creating a work center with all required fields"""
        wc = WorkCenter(
            organization_id=1,
            plant_id=101,
            work_center_code="WC001",
            work_center_name="Assembly Line 1",
            work_center_type=WorkCenterType.ASSEMBLY,
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=True
        )
        db_session.add(wc)
        db_session.commit()

        assert wc.id is not None
        assert wc.organization_id == 1
        assert wc.plant_id == 101
        assert wc.work_center_code == "WC001"
        assert wc.work_center_name == "Assembly Line 1"
        assert wc.work_center_type == WorkCenterType.ASSEMBLY
        assert wc.capacity_per_hour == 10.0
        assert wc.cost_per_hour == 50.0
        assert wc.is_active is True
        assert wc.created_at is not None

    def test_work_center_types(self, db_session):
        """Test all valid work center types"""
        types = [
            WorkCenterType.MACHINE,
            WorkCenterType.ASSEMBLY,
            WorkCenterType.PACKAGING,
            WorkCenterType.QUALITY_CHECK
        ]

        for idx, wc_type in enumerate(types):
            wc = WorkCenter(
                organization_id=1,
                plant_id=101,
                work_center_code=f"WC{idx:03d}",
                work_center_name=f"Work Center {wc_type.value}",
                work_center_type=wc_type,
                capacity_per_hour=10.0,
                cost_per_hour=50.0,
                is_active=True
            )
            db_session.add(wc)

        db_session.commit()
        assert db_session.query(WorkCenter).count() == 4

    def test_work_center_code_unique_per_plant(self, db_session):
        """Test that work_center_code is unique per plant"""
        wc1 = WorkCenter(
            organization_id=1,
            plant_id=101,
            work_center_code="WC001",
            work_center_name="Work Center 1",
            work_center_type=WorkCenterType.MACHINE,
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=True
        )
        db_session.add(wc1)
        db_session.commit()

        # Same code, same org, same plant - should fail
        wc2 = WorkCenter(
            organization_id=1,
            plant_id=101,
            work_center_code="WC001",
            work_center_name="Work Center 2",
            work_center_type=WorkCenterType.ASSEMBLY,
            capacity_per_hour=15.0,
            cost_per_hour=60.0,
            is_active=True
        )
        db_session.add(wc2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_work_center_code_different_plants(self, db_session):
        """Test that work_center_code can be same across different plants"""
        wc1 = WorkCenter(
            organization_id=1,
            plant_id=101,
            work_center_code="WC001",
            work_center_name="Work Center Plant 101",
            work_center_type=WorkCenterType.MACHINE,
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=True
        )
        db_session.add(wc1)
        db_session.commit()

        # Same code, different plant - should succeed
        wc2 = WorkCenter(
            organization_id=1,
            plant_id=102,
            work_center_code="WC001",
            work_center_name="Work Center Plant 102",
            work_center_type=WorkCenterType.ASSEMBLY,
            capacity_per_hour=15.0,
            cost_per_hour=60.0,
            is_active=True
        )
        db_session.add(wc2)
        db_session.commit()

        assert wc1.work_center_code == wc2.work_center_code
        assert wc1.plant_id != wc2.plant_id

    def test_work_center_capacity_validation(self, db_session):
        """Test that capacity_per_hour must be positive"""
        # This will be tested at application level
        # For now, just verify field accepts positive values
        wc = WorkCenter(
            organization_id=1,
            plant_id=101,
            work_center_code="WC001",
            work_center_name="Work Center 1",
            work_center_type=WorkCenterType.MACHINE,
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=True
        )
        db_session.add(wc)
        db_session.commit()

        assert wc.capacity_per_hour > 0

    def test_work_center_repr(self, db_session):
        """Test WorkCenter __repr__ method"""
        wc = WorkCenter(
            organization_id=1,
            plant_id=101,
            work_center_code="WC001",
            work_center_name="Assembly Line",
            work_center_type=WorkCenterType.ASSEMBLY,
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=True
        )
        db_session.add(wc)
        db_session.commit()

        repr_str = repr(wc)
        assert "WorkCenter" in repr_str
        assert "WC001" in repr_str


class TestWorkOrder:
    """Test WorkOrder entity"""

    def test_create_work_order(self, db_session, setup_dependencies):
        """Test creating a work order with all required fields"""
        deps = setup_dependencies

        wo = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(wo)
        db_session.commit()

        assert wo.id is not None
        assert wo.organization_id == 1
        assert wo.plant_id == 101
        assert wo.work_order_number == "WO2024-001"
        assert wo.material_id == deps['material'].id
        assert wo.order_type == OrderType.PRODUCTION
        assert wo.order_status == OrderStatus.PLANNED
        assert wo.planned_quantity == 100.0
        assert wo.actual_quantity == 0.0
        assert wo.priority == 5
        assert wo.created_at is not None

    def test_work_order_types(self, db_session, setup_dependencies):
        """Test all valid work order types"""
        deps = setup_dependencies
        types = [OrderType.PRODUCTION, OrderType.REWORK, OrderType.ASSEMBLY]

        for idx, order_type in enumerate(types):
            wo = WorkOrder(
                organization_id=1,
                plant_id=101,
                work_order_number=f"WO-{order_type.value}-{idx:03d}",
                material_id=deps['material'].id,
                order_type=order_type,
                order_status=OrderStatus.PLANNED,
                planned_quantity=100.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=5),
                priority=5,
                created_by_user_id=1
            )
            db_session.add(wo)

        db_session.commit()
        assert db_session.query(WorkOrder).count() == 3

    def test_work_order_statuses(self, db_session, setup_dependencies):
        """Test all valid work order statuses"""
        deps = setup_dependencies
        statuses = [
            OrderStatus.PLANNED,
            OrderStatus.RELEASED,
            OrderStatus.IN_PROGRESS,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED
        ]

        for idx, status in enumerate(statuses):
            wo = WorkOrder(
                organization_id=1,
                plant_id=101,
                work_order_number=f"WO-{status.value}-{idx:03d}",
                material_id=deps['material'].id,
                order_type=OrderType.PRODUCTION,
                order_status=status,
                planned_quantity=100.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=5),
                priority=5,
                created_by_user_id=1
            )
            db_session.add(wo)

        db_session.commit()
        assert db_session.query(WorkOrder).count() == 5

    def test_work_order_number_unique_per_plant(self, db_session, setup_dependencies):
        """Test that work_order_number is unique per organization/plant"""
        deps = setup_dependencies

        wo1 = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(wo1)
        db_session.commit()

        # Same number, same org, same plant - should fail
        wo2 = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.REWORK,
            order_status=OrderStatus.PLANNED,
            planned_quantity=50.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=3),
            priority=3,
            created_by_user_id=1
        )
        db_session.add(wo2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_work_order_priority_range(self, db_session, setup_dependencies):
        """Test that priority is between 1 and 10"""
        deps = setup_dependencies

        # Valid priorities: 1, 5, 10
        for priority in [1, 5, 10]:
            wo = WorkOrder(
                organization_id=1,
                plant_id=101,
                work_order_number=f"WO-PRI{priority}",
                material_id=deps['material'].id,
                order_type=OrderType.PRODUCTION,
                order_status=OrderStatus.PLANNED,
                planned_quantity=100.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=5),
                priority=priority,
                created_by_user_id=1
            )
            db_session.add(wo)

        db_session.commit()
        assert db_session.query(WorkOrder).count() == 3

    def test_work_order_foreign_keys(self, db_engine):
        """Test that foreign key constraints exist"""
        inspector = inspect(db_engine)
        fks = inspector.get_foreign_keys('work_order')

        # Should have FK to material
        fk_tables = [fk['referred_table'] for fk in fks]
        assert 'material' in fk_tables

    def test_work_order_indexes(self, db_engine):
        """Test that proper indexes exist on work_order table"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('work_order')

        # Collect all indexed columns
        index_columns = []
        for idx in indexes:
            index_columns.extend(idx['column_names'])

        assert 'work_order_number' in index_columns
        assert 'order_status' in index_columns
        assert 'material_id' in index_columns
        assert 'organization_id' in index_columns
        assert 'plant_id' in index_columns

    def test_work_order_repr(self, db_session, setup_dependencies):
        """Test WorkOrder __repr__ method"""
        deps = setup_dependencies

        wo = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(wo)
        db_session.commit()

        repr_str = repr(wo)
        assert "WorkOrder" in repr_str
        assert "WO2024-001" in repr_str


class TestWorkOrderOperation:
    """Test WorkOrderOperation entity"""

    def test_create_operation(self, db_session, setup_dependencies):
        """Test creating a work order operation"""
        deps = setup_dependencies

        # Create work order first
        wo = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(wo)
        db_session.commit()

        # Create operation
        op = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=wo.id,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=deps['work_center'].id,
            setup_time_minutes=30.0,
            run_time_per_unit_minutes=5.0,
            status=OperationStatus.PENDING
        )
        db_session.add(op)
        db_session.commit()

        assert op.id is not None
        assert op.work_order_id == wo.id
        assert op.operation_number == 10
        assert op.operation_name == "Assembly"
        assert op.work_center_id == deps['work_center'].id
        assert op.setup_time_minutes == 30.0
        assert op.run_time_per_unit_minutes == 5.0
        assert op.status == OperationStatus.PENDING

    def test_operation_statuses(self, db_session, setup_dependencies):
        """Test all valid operation statuses"""
        deps = setup_dependencies

        wo = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(wo)
        db_session.commit()

        statuses = [
            OperationStatus.PENDING,
            OperationStatus.IN_PROGRESS,
            OperationStatus.COMPLETED,
            OperationStatus.SKIPPED
        ]

        for idx, status in enumerate(statuses):
            op = WorkOrderOperation(
                organization_id=1,
                plant_id=101,
                work_order_id=wo.id,
                operation_number=(idx + 1) * 10,
                operation_name=f"Operation {status.value}",
                work_center_id=deps['work_center'].id,
                setup_time_minutes=30.0,
                run_time_per_unit_minutes=5.0,
                status=status
            )
            db_session.add(op)

        db_session.commit()
        assert db_session.query(WorkOrderOperation).count() == 4

    def test_operation_number_unique_per_work_order(self, db_session, setup_dependencies):
        """Test that operation_number is unique per work order"""
        deps = setup_dependencies

        wo = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(wo)
        db_session.commit()

        op1 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=wo.id,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=deps['work_center'].id,
            setup_time_minutes=30.0,
            run_time_per_unit_minutes=5.0,
            status=OperationStatus.PENDING
        )
        db_session.add(op1)
        db_session.commit()

        # Same operation number, same work order - should fail
        op2 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=wo.id,
            operation_number=10,
            operation_name="Different Operation",
            work_center_id=deps['work_center'].id,
            setup_time_minutes=20.0,
            run_time_per_unit_minutes=3.0,
            status=OperationStatus.PENDING
        )
        db_session.add(op2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_operation_sequence_ordering(self, db_session, setup_dependencies):
        """Test that operations can be ordered by operation_number"""
        deps = setup_dependencies

        wo = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(wo)
        db_session.commit()

        # Create operations in non-sequential order
        operations = [
            (30, "Packaging"),
            (10, "Assembly"),
            (20, "Quality Check")
        ]

        for op_num, op_name in operations:
            op = WorkOrderOperation(
                organization_id=1,
                plant_id=101,
                work_order_id=wo.id,
                operation_number=op_num,
                operation_name=op_name,
                work_center_id=deps['work_center'].id,
                setup_time_minutes=30.0,
                run_time_per_unit_minutes=5.0,
                status=OperationStatus.PENDING
            )
            db_session.add(op)

        db_session.commit()

        # Retrieve operations in order
        ops = db_session.query(WorkOrderOperation)\
            .filter_by(work_order_id=wo.id)\
            .order_by(WorkOrderOperation.operation_number)\
            .all()

        assert len(ops) == 3
        assert ops[0].operation_number == 10
        assert ops[1].operation_number == 20
        assert ops[2].operation_number == 30


class TestWorkOrderMaterial:
    """Test WorkOrderMaterial entity"""

    def test_create_work_order_material(self, db_session, setup_dependencies):
        """Test creating a work order material consumption record"""
        deps = setup_dependencies

        # Create raw material
        raw_mat = Material(
            organization_id=1,
            plant_id=101,
            material_number="RM001",
            material_name="Raw Material A",
            description="Test raw material",
            material_category_id=deps['category'].id,
            base_uom_id=deps['uom'].id,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=50.0,
            reorder_point=25.0,
            lot_size=100.0,
            lead_time_days=3,
            is_active=True
        )
        db_session.add(raw_mat)
        db_session.commit()

        # Create work order
        wo = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(wo)
        db_session.commit()

        # Create work order material
        wom = WorkOrderMaterial(
            work_order_id=wo.id,
            material_id=raw_mat.id,
            planned_quantity=200.0,
            actual_quantity=0.0,
            unit_of_measure_id=deps['uom'].id,
            backflush=True
        )
        db_session.add(wom)
        db_session.commit()

        assert wom.id is not None
        assert wom.work_order_id == wo.id
        assert wom.material_id == raw_mat.id
        assert wom.planned_quantity == 200.0
        assert wom.actual_quantity == 0.0
        assert wom.unit_of_measure_id == deps['uom'].id
        assert wom.backflush is True

    def test_work_order_material_backflush_flag(self, db_session, setup_dependencies):
        """Test backflush flag for auto-consumption"""
        deps = setup_dependencies

        # Create materials
        raw_mat1 = Material(
            organization_id=1,
            plant_id=101,
            material_number="RM001",
            material_name="Raw Material A",
            description="Test raw material",
            material_category_id=deps['category'].id,
            base_uom_id=deps['uom'].id,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=50.0,
            reorder_point=25.0,
            lot_size=100.0,
            lead_time_days=3,
            is_active=True
        )
        raw_mat2 = Material(
            organization_id=1,
            plant_id=101,
            material_number="RM002",
            material_name="Raw Material B",
            description="Test raw material",
            material_category_id=deps['category'].id,
            base_uom_id=deps['uom'].id,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=30.0,
            reorder_point=15.0,
            lot_size=50.0,
            lead_time_days=2,
            is_active=True
        )
        db_session.add_all([raw_mat1, raw_mat2])
        db_session.commit()

        # Create work order
        wo = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(wo)
        db_session.commit()

        # Create work order materials - one backflush, one manual
        wom1 = WorkOrderMaterial(
            work_order_id=wo.id,
            material_id=raw_mat1.id,
            planned_quantity=200.0,
            actual_quantity=0.0,
            unit_of_measure_id=deps['uom'].id,
            backflush=True  # Auto-consume
        )
        wom2 = WorkOrderMaterial(
            work_order_id=wo.id,
            material_id=raw_mat2.id,
            planned_quantity=100.0,
            actual_quantity=0.0,
            unit_of_measure_id=deps['uom'].id,
            backflush=False  # Manual consumption
        )
        db_session.add_all([wom1, wom2])
        db_session.commit()

        # Verify backflush flags
        backflush_materials = db_session.query(WorkOrderMaterial)\
            .filter_by(work_order_id=wo.id, backflush=True)\
            .all()
        manual_materials = db_session.query(WorkOrderMaterial)\
            .filter_by(work_order_id=wo.id, backflush=False)\
            .all()

        assert len(backflush_materials) == 1
        assert len(manual_materials) == 1
        assert backflush_materials[0].material_id == raw_mat1.id
        assert manual_materials[0].material_id == raw_mat2.id
