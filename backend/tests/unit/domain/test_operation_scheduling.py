"""
Unit tests for Operation Scheduling Service.
Following TDD approach: RED -> GREEN -> REFACTOR

Tests cover:
- Sequential scheduling (operations complete before next starts)
- Overlap scheduling (operations start during predecessor execution)
- Parallel scheduling (multiple operations run simultaneously)
- Dependency validation
- Gantt chart data generation
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.work_order import (
    WorkOrder,
    WorkOrderOperation,
    WorkCenter,
    OrderType,
    OrderStatus,
    OperationStatus,
    WorkCenterType,
    SchedulingMode
)
from app.models.material import Material, MaterialCategory, UnitOfMeasure
from app.models.operation_config import OperationSchedulingConfig
from app.domain.services.operation_scheduling_service import (
    OperationSchedulingService,
    ScheduledOperation,
    GanttChartData
)


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

    # Create Material
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

    # Create WorkCenters
    work_center_1 = WorkCenter(
        organization_id=1,
        plant_id=101,
        work_center_code="WC001",
        work_center_name="Cutting Line",
        work_center_type=WorkCenterType.MACHINE,
        capacity_per_hour=10.0,
        cost_per_hour=50.0,
        is_active=True
    )
    work_center_2 = WorkCenter(
        organization_id=1,
        plant_id=101,
        work_center_code="WC002",
        work_center_name="Assembly Line",
        work_center_type=WorkCenterType.ASSEMBLY,
        capacity_per_hour=8.0,
        cost_per_hour=60.0,
        is_active=True
    )
    db_session.add_all([work_center_1, work_center_2])
    db_session.commit()

    return {
        'uom': uom,
        'category': category,
        'material': material,
        'work_center_1': work_center_1,
        'work_center_2': work_center_2
    }


@pytest.fixture
def work_order_with_operations(db_session, setup_dependencies):
    """Create a work order with sequential operations"""
    deps = setup_dependencies

    work_order = WorkOrder(
        organization_id=1,
        plant_id=101,
        work_order_number="WO-2025-001",
        material_id=deps['material'].id,
        order_type=OrderType.PRODUCTION,
        order_status=OrderStatus.PLANNED,
        planned_quantity=100.0,
        actual_quantity=0.0,
        start_date_planned=datetime.utcnow(),
        end_date_planned=datetime.utcnow() + timedelta(days=2),
        priority=5,
        created_by_user_id=1
    )
    db_session.add(work_order)
    db_session.commit()

    # Operation 1: Cutting (60 minutes setup + 2 min/unit)
    op1 = WorkOrderOperation(
        organization_id=1,
        plant_id=101,
        work_order_id=work_order.id,
        operation_number=10,
        operation_name="Cutting",
        work_center_id=deps['work_center_1'].id,
        setup_time_minutes=60.0,
        run_time_per_unit_minutes=2.0,
        status=OperationStatus.PENDING,
        scheduling_mode=SchedulingMode.SEQUENTIAL,
        overlap_percentage=0.0,
        predecessor_operation_id=None,
        can_start_at_percentage=0.0
    )

    # Operation 2: Assembly (30 minutes setup + 3 min/unit)
    op2 = WorkOrderOperation(
        organization_id=1,
        plant_id=101,
        work_order_id=work_order.id,
        operation_number=20,
        operation_name="Assembly",
        work_center_id=deps['work_center_2'].id,
        setup_time_minutes=30.0,
        run_time_per_unit_minutes=3.0,
        status=OperationStatus.PENDING,
        scheduling_mode=SchedulingMode.SEQUENTIAL,
        overlap_percentage=0.0,
        predecessor_operation_id=None,  # Will be set to op1.id after commit
        can_start_at_percentage=100.0
    )

    db_session.add_all([op1, op2])
    db_session.commit()

    # Update predecessor relationship
    op2.predecessor_operation_id = op1.id
    db_session.commit()

    return work_order


class TestSequentialScheduling:
    """Test sequential scheduling mode - operations complete before next starts"""

    def test_sequential_scheduling_basic(self, db_session, work_order_with_operations):
        """
        RED TEST: Sequential scheduling ensures operations don't overlap.
        Operation 2 starts only after Operation 1 completes.
        """
        service = OperationSchedulingService(db_session)
        start_date = datetime(2025, 11, 10, 8, 0, 0)  # 8 AM start

        # Schedule operations for 100 units
        scheduled_ops = service.schedule_operations(
            work_order_id=work_order_with_operations.id,
            start_date=start_date,
            quantity=100.0
        )

        # Verify we have 2 scheduled operations
        assert len(scheduled_ops) == 2

        # Operation 1: 60 min setup + (100 units * 2 min) = 260 minutes total
        op1 = scheduled_ops[0]
        assert op1.operation_number == 10
        assert op1.start_time == start_date
        expected_end_op1 = start_date + timedelta(minutes=260)
        assert op1.end_time == expected_end_op1

        # Operation 2: Should start when Operation 1 ends (SEQUENTIAL)
        # 30 min setup + (100 units * 3 min) = 330 minutes total
        op2 = scheduled_ops[1]
        assert op2.operation_number == 20
        assert op2.start_time == expected_end_op1  # Starts when op1 ends
        expected_end_op2 = expected_end_op1 + timedelta(minutes=330)
        assert op2.end_time == expected_end_op2

    def test_sequential_scheduling_no_gaps(self, db_session, work_order_with_operations):
        """
        RED TEST: Sequential scheduling should have no time gaps between operations.
        """
        service = OperationSchedulingService(db_session)
        start_date = datetime(2025, 11, 10, 8, 0, 0)

        scheduled_ops = service.schedule_operations(
            work_order_id=work_order_with_operations.id,
            start_date=start_date,
            quantity=100.0
        )

        # Verify no gap: op2 start = op1 end
        op1_end = scheduled_ops[0].end_time
        op2_start = scheduled_ops[1].start_time
        assert op2_start == op1_end  # No gap


class TestOverlapScheduling:
    """Test overlap scheduling mode - operations can start during predecessor execution"""

    def test_overlap_scheduling_50_percent(self, db_session, setup_dependencies):
        """
        RED TEST: Overlap scheduling at 50% allows operation to start when
        predecessor is 50% complete.
        """
        deps = setup_dependencies

        work_order = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO-2025-002",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.utcnow(),
            end_date_planned=datetime.utcnow() + timedelta(days=2),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        # Operation 1: 60 min setup + 200 min run = 260 min total
        op1 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=10,
            operation_name="Cutting",
            work_center_id=deps['work_center_1'].id,
            setup_time_minutes=60.0,
            run_time_per_unit_minutes=2.0,
            status=OperationStatus.PENDING,
            scheduling_mode=SchedulingMode.SEQUENTIAL,
            overlap_percentage=0.0,
            predecessor_operation_id=None,
            can_start_at_percentage=0.0
        )

        # Operation 2: Can start when Operation 1 is 50% complete
        op2 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=20,
            operation_name="Assembly",
            work_center_id=deps['work_center_2'].id,
            setup_time_minutes=30.0,
            run_time_per_unit_minutes=3.0,
            status=OperationStatus.PENDING,
            scheduling_mode=SchedulingMode.OVERLAP,
            overlap_percentage=50.0,
            predecessor_operation_id=None,
            can_start_at_percentage=50.0
        )

        db_session.add_all([op1, op2])
        db_session.commit()

        op2.predecessor_operation_id = op1.id
        db_session.commit()

        service = OperationSchedulingService(db_session)
        start_date = datetime(2025, 11, 10, 8, 0, 0)

        scheduled_ops = service.schedule_operations(
            work_order_id=work_order.id,
            start_date=start_date,
            quantity=100.0
        )

        # Operation 1: 260 minutes total
        op1_sched = scheduled_ops[0]
        assert op1_sched.start_time == start_date
        assert op1_sched.end_time == start_date + timedelta(minutes=260)

        # Operation 2: Should start when op1 is 50% complete (130 minutes in)
        op2_sched = scheduled_ops[1]
        expected_op2_start = start_date + timedelta(minutes=130)  # 50% of 260
        assert op2_sched.start_time == expected_op2_start

    def test_overlap_scheduling_75_percent(self, db_session, setup_dependencies):
        """
        RED TEST: Overlap at 75% - operation starts when predecessor is 75% complete.
        """
        deps = setup_dependencies

        work_order = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO-2025-003",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        op1 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=10,
            operation_name="Cutting",
            work_center_id=deps['work_center_1'].id,
            setup_time_minutes=40.0,
            run_time_per_unit_minutes=2.0,
            status=OperationStatus.PENDING,
            scheduling_mode=SchedulingMode.SEQUENTIAL
        )

        op2 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=20,
            operation_name="Assembly",
            work_center_id=deps['work_center_2'].id,
            setup_time_minutes=20.0,
            run_time_per_unit_minutes=1.5,
            status=OperationStatus.PENDING,
            scheduling_mode=SchedulingMode.OVERLAP,
            overlap_percentage=75.0,
            can_start_at_percentage=75.0
        )

        db_session.add_all([op1, op2])
        db_session.commit()

        op2.predecessor_operation_id = op1.id
        db_session.commit()

        service = OperationSchedulingService(db_session)
        start_date = datetime(2025, 11, 10, 9, 0, 0)

        scheduled_ops = service.schedule_operations(
            work_order_id=work_order.id,
            start_date=start_date,
            quantity=100.0
        )

        # Operation 1: 40 + 200 = 240 minutes
        # 75% of 240 = 180 minutes
        expected_op2_start = start_date + timedelta(minutes=180)
        assert scheduled_ops[1].start_time == expected_op2_start


class TestParallelScheduling:
    """Test parallel scheduling mode - multiple operations run simultaneously"""

    def test_parallel_scheduling_same_start(self, db_session, setup_dependencies):
        """
        RED TEST: Parallel operations should start at the same time.
        """
        deps = setup_dependencies

        work_order = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO-2025-004",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=50.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        # Two parallel operations
        op1 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=10,
            operation_name="Quality Check",
            work_center_id=deps['work_center_1'].id,
            setup_time_minutes=10.0,
            run_time_per_unit_minutes=1.0,
            status=OperationStatus.PENDING,
            scheduling_mode=SchedulingMode.PARALLEL,
            predecessor_operation_id=None
        )

        op2 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=20,
            operation_name="Packaging",
            work_center_id=deps['work_center_2'].id,
            setup_time_minutes=15.0,
            run_time_per_unit_minutes=2.0,
            status=OperationStatus.PENDING,
            scheduling_mode=SchedulingMode.PARALLEL,
            predecessor_operation_id=None
        )

        db_session.add_all([op1, op2])
        db_session.commit()

        service = OperationSchedulingService(db_session)
        start_date = datetime(2025, 11, 10, 10, 0, 0)

        scheduled_ops = service.schedule_operations(
            work_order_id=work_order.id,
            start_date=start_date,
            quantity=50.0
        )

        # Both operations should start at the same time
        assert scheduled_ops[0].start_time == start_date
        assert scheduled_ops[1].start_time == start_date

        # But they can have different end times based on duration
        # Op1: 10 + 50 = 60 minutes
        # Op2: 15 + 100 = 115 minutes
        assert scheduled_ops[0].end_time == start_date + timedelta(minutes=60)
        assert scheduled_ops[1].end_time == start_date + timedelta(minutes=115)


class TestDependencyValidation:
    """Test dependency validation logic"""

    def test_dependency_validation_prevents_cyclic_dependencies(self, db_session, setup_dependencies):
        """
        RED TEST: Service should detect and reject cyclic dependencies.
        """
        deps = setup_dependencies

        work_order = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO-2025-005",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        op1 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=10,
            operation_name="Op1",
            work_center_id=deps['work_center_1'].id,
            setup_time_minutes=10.0,
            run_time_per_unit_minutes=1.0,
            status=OperationStatus.PENDING
        )

        op2 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=20,
            operation_name="Op2",
            work_center_id=deps['work_center_2'].id,
            setup_time_minutes=10.0,
            run_time_per_unit_minutes=1.0,
            status=OperationStatus.PENDING
        )

        db_session.add_all([op1, op2])
        db_session.commit()

        # Create cyclic dependency: op1 -> op2 -> op1
        op1.predecessor_operation_id = op2.id
        op2.predecessor_operation_id = op1.id
        db_session.commit()

        service = OperationSchedulingService(db_session)
        start_date = datetime(2025, 11, 10, 8, 0, 0)

        # Should raise error for cyclic dependency
        with pytest.raises(ValueError, match="Cyclic dependency detected"):
            service.schedule_operations(
                work_order_id=work_order.id,
                start_date=start_date,
                quantity=100.0
            )

    def test_dependency_validation_invalid_predecessor(self, db_session, setup_dependencies):
        """
        RED TEST: Service should validate predecessor exists in same work order.
        """
        deps = setup_dependencies

        work_order = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO-2025-006",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        op1 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=10,
            operation_name="Op1",
            work_center_id=deps['work_center_1'].id,
            setup_time_minutes=10.0,
            run_time_per_unit_minutes=1.0,
            status=OperationStatus.PENDING,
            predecessor_operation_id=99999  # Invalid predecessor
        )

        db_session.add(op1)
        db_session.commit()

        service = OperationSchedulingService(db_session)
        start_date = datetime(2025, 11, 10, 8, 0, 0)

        with pytest.raises(ValueError, match="Invalid predecessor operation"):
            service.schedule_operations(
                work_order_id=work_order.id,
                start_date=start_date,
                quantity=100.0
            )


class TestGanttChartDataGeneration:
    """Test Gantt chart data structure generation"""

    def test_gantt_chart_data_structure(self, db_session, work_order_with_operations):
        """
        RED TEST: Service should generate Gantt chart compatible data.
        """
        service = OperationSchedulingService(db_session)
        start_date = datetime(2025, 11, 10, 8, 0, 0)

        gantt_data = service.generate_gantt_chart_data(
            work_order_id=work_order_with_operations.id,
            start_date=start_date,
            quantity=100.0
        )

        # Verify structure
        assert isinstance(gantt_data, GanttChartData)
        assert gantt_data.work_order_id == work_order_with_operations.id
        assert gantt_data.work_order_number == "WO-2025-001"
        assert len(gantt_data.tasks) == 2

        # Verify task structure
        task1 = gantt_data.tasks[0]
        assert task1['id'] is not None
        assert task1['name'] == "Cutting"
        assert task1['operation_number'] == 10
        assert task1['work_center'] == "WC001"
        assert 'start' in task1
        assert 'end' in task1
        assert 'duration_minutes' in task1
        assert task1['scheduling_mode'] == 'SEQUENTIAL'

    def test_gantt_chart_with_overlaps(self, db_session, setup_dependencies):
        """
        RED TEST: Gantt chart should show overlap relationships correctly.
        """
        deps = setup_dependencies

        work_order = WorkOrder(
            organization_id=1,
            plant_id=101,
            work_order_number="WO-2025-007",
            material_id=deps['material'].id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        op1 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=10,
            operation_name="Cutting",
            work_center_id=deps['work_center_1'].id,
            setup_time_minutes=60.0,
            run_time_per_unit_minutes=2.0,
            status=OperationStatus.PENDING,
            scheduling_mode=SchedulingMode.SEQUENTIAL
        )

        op2 = WorkOrderOperation(
            organization_id=1,
            plant_id=101,
            work_order_id=work_order.id,
            operation_number=20,
            operation_name="Assembly",
            work_center_id=deps['work_center_2'].id,
            setup_time_minutes=30.0,
            run_time_per_unit_minutes=3.0,
            status=OperationStatus.PENDING,
            scheduling_mode=SchedulingMode.OVERLAP,
            overlap_percentage=60.0,
            can_start_at_percentage=60.0
        )

        db_session.add_all([op1, op2])
        db_session.commit()

        op2.predecessor_operation_id = op1.id
        db_session.commit()

        service = OperationSchedulingService(db_session)
        start_date = datetime(2025, 11, 10, 8, 0, 0)

        gantt_data = service.generate_gantt_chart_data(
            work_order_id=work_order.id,
            start_date=start_date,
            quantity=100.0
        )

        # Verify overlap is represented
        task1 = gantt_data.tasks[0]
        task2 = gantt_data.tasks[1]

        assert task2['predecessor_id'] == task1['id']
        assert task2['overlap_percentage'] == 60.0
        assert task2['start'] < task1['end']  # Overlaps


class TestOperationSchedulingConfig:
    """Test operation scheduling configuration per work center and organization"""

    def test_default_config_creation(self, db_session):
        """
        RED TEST: Should create default scheduling config for organization/plant.
        """
        config = OperationSchedulingConfig(
            organization_id=1,
            plant_id=101,
            work_center_id=None,  # Global config
            default_scheduling_mode=SchedulingMode.SEQUENTIAL,
            default_overlap_percentage=0.0,
            allow_parallel_operations=False
        )
        db_session.add(config)
        db_session.commit()

        assert config.id is not None
        assert config.default_scheduling_mode == SchedulingMode.SEQUENTIAL
        assert config.default_overlap_percentage == 0.0

    def test_work_center_specific_config(self, db_session, setup_dependencies):
        """
        RED TEST: Should support work center specific scheduling configuration.
        """
        deps = setup_dependencies

        config = OperationSchedulingConfig(
            organization_id=1,
            plant_id=101,
            work_center_id=deps['work_center_1'].id,
            default_scheduling_mode=SchedulingMode.OVERLAP,
            default_overlap_percentage=50.0,
            allow_parallel_operations=True
        )
        db_session.add(config)
        db_session.commit()

        assert config.work_center_id == deps['work_center_1'].id
        assert config.default_scheduling_mode == SchedulingMode.OVERLAP
        assert config.default_overlap_percentage == 50.0
