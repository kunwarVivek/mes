"""
Unit tests for Production Scheduling Service.
Phase 3: Production Planning Module - Component 6
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.application.services.production_scheduling_service import ProductionSchedulingService
from app.models.work_order import (
    WorkOrder, WorkOrderOperation, WorkCenter,
    OrderType, OrderStatus, OperationStatus, WorkCenterType
)


class TestProductionSchedulingService:
    """Test ProductionSchedulingService application service"""

    @pytest.fixture
    def db_session(self):
        """Mock database session"""
        session = MagicMock(spec=Session)
        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.filter.return_value.first.return_value = None
        return session

    @pytest.fixture
    def scheduling_service(self, db_session):
        """Create ProductionSchedulingService instance"""
        return ProductionSchedulingService(db_session)

    @pytest.fixture
    def sample_work_center(self):
        """Create sample work center"""
        return WorkCenter(
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

    @pytest.fixture
    def sample_work_order(self):
        """Create sample work order"""
        return WorkOrder(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-001",
            material_id=100,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=10.0,
            actual_quantity=0.0,
            end_date_planned=datetime(2025, 1, 20),
            priority=5,
            created_by_user_id=1
        )

    @pytest.fixture
    def sample_operation(self, sample_work_center):
        """Create sample operation"""
        return WorkOrderOperation(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_id=1,
            operation_number=10,
            operation_name="Assembly Operation",
            work_center_id=1,
            setup_time_minutes=30.0,
            run_time_per_unit_minutes=3.0,
            status=OperationStatus.PENDING,
            work_center=sample_work_center
        )

    def test_schedule_work_orders_earliest_due_date_strategy(
        self, scheduling_service, db_session, sample_work_order, sample_operation, sample_work_center
    ):
        """Should schedule work orders using EARLIEST_DUE_DATE strategy"""
        # Setup: Create 3 work orders with different due dates
        wo1 = WorkOrder(
            id=1, organization_id=1, plant_id=1, work_order_number="WO-001",
            material_id=100, order_type=OrderType.PRODUCTION, order_status=OrderStatus.PLANNED,
            planned_quantity=10.0, end_date_planned=datetime(2025, 1, 20), priority=5, created_by_user_id=1
        )
        wo2 = WorkOrder(
            id=2, organization_id=1, plant_id=1, work_order_number="WO-002",
            material_id=101, order_type=OrderType.PRODUCTION, order_status=OrderStatus.PLANNED,
            planned_quantity=5.0, end_date_planned=datetime(2025, 1, 15), priority=5, created_by_user_id=1
        )
        wo3 = WorkOrder(
            id=3, organization_id=1, plant_id=1, work_order_number="WO-003",
            material_id=102, order_type=OrderType.PRODUCTION, order_status=OrderStatus.PLANNED,
            planned_quantity=8.0, end_date_planned=datetime(2025, 1, 25), priority=5, created_by_user_id=1
        )

        op1 = WorkOrderOperation(
            id=1, organization_id=1, plant_id=1, work_order_id=1, operation_number=10,
            operation_name="Op 10", work_center_id=1, setup_time_minutes=30.0,
            run_time_per_unit_minutes=3.0, status=OperationStatus.PENDING, work_center=sample_work_center
        )
        op2 = WorkOrderOperation(
            id=2, organization_id=1, plant_id=1, work_order_id=2, operation_number=10,
            operation_name="Op 10", work_center_id=1, setup_time_minutes=20.0,
            run_time_per_unit_minutes=2.0, status=OperationStatus.PENDING, work_center=sample_work_center
        )
        op3 = WorkOrderOperation(
            id=3, organization_id=1, plant_id=1, work_order_id=3, operation_number=10,
            operation_name="Op 10", work_center_id=1, setup_time_minutes=40.0,
            run_time_per_unit_minutes=4.0, status=OperationStatus.PENDING, work_center=sample_work_center
        )

        wo1.operations = [op1]
        wo2.operations = [op2]
        wo3.operations = [op3]

        # Mock database queries
        db_session.query.return_value.filter.return_value.all.return_value = [wo1, wo2, wo3]
        db_session.query.return_value.filter.return_value.first.return_value = sample_work_center

        # Test: Schedule work orders
        schedule = scheduling_service.schedule_work_orders(
            work_order_ids=[1, 2, 3],
            scheduling_strategy='EARLIEST_DUE_DATE'
        )

        # Assert: Schedule created with operations in correct order
        assert schedule is not None
        assert schedule.status == 'DRAFT'
        assert len(schedule.scheduled_operations) == 3

        # Should be scheduled in order: WO-002 (Jan 15), WO-001 (Jan 20), WO-003 (Jan 25)
        sorted_ops = sorted(schedule.scheduled_operations, key=lambda x: x.scheduled_start)
        assert sorted_ops[0].work_order_operation_id == 2  # WO-002 op
        assert sorted_ops[1].work_order_operation_id == 1  # WO-001 op
        assert sorted_ops[2].work_order_operation_id == 3  # WO-003 op

    def test_schedule_single_operation_finds_available_slot(
        self, scheduling_service, db_session, sample_work_center, sample_operation, sample_work_order
    ):
        """Should find available time slot and schedule single operation"""
        # Mock: Work center with existing operation from 08:00-10:00
        existing_op = WorkOrderOperation(
            id=10, organization_id=1, plant_id=1, work_order_id=5, operation_number=10,
            operation_name="Existing", work_center_id=1, setup_time_minutes=30.0,
            run_time_per_unit_minutes=5.0, status=OperationStatus.IN_PROGRESS,
            start_time=datetime(2025, 1, 10, 8, 0),
            end_time=datetime(2025, 1, 10, 10, 0),
            work_center=sample_work_center
        )

        # Create operation with work order relationship
        sample_operation.work_order = sample_work_order

        # Mock database queries - need to handle multiple query calls
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == WorkOrderOperation:
                mock_query.filter.return_value.first.return_value = sample_operation
                mock_query.filter.return_value.order_by.return_value.all.return_value = [existing_op]
            elif model == WorkCenter:
                mock_query.filter.return_value.first.return_value = sample_work_center
            return mock_query

        db_session.query.side_effect = query_side_effect

        # Test: Schedule new operation
        scheduled_start = scheduling_service.schedule_single_operation(
            operation_id=1,
            preferred_start=datetime(2025, 1, 10, 8, 0)
        )

        # Assert: Should schedule after existing operation (10:00 or later)
        assert scheduled_start >= datetime(2025, 1, 10, 10, 0)

    def test_calculate_critical_path_identifies_longest_path(
        self, scheduling_service, db_session, sample_work_order, sample_work_center
    ):
        """Should calculate critical path through work order operations"""
        # Setup: Work order with 3 sequential operations
        op1 = WorkOrderOperation(
            id=1, organization_id=1, plant_id=1, work_order_id=1, operation_number=10,
            operation_name="Cut", work_center_id=1, setup_time_minutes=30.0,
            run_time_per_unit_minutes=5.0, status=OperationStatus.PENDING, work_center=sample_work_center
        )
        op2 = WorkOrderOperation(
            id=2, organization_id=1, plant_id=1, work_order_id=1, operation_number=20,
            operation_name="Assemble", work_center_id=1, setup_time_minutes=45.0,
            run_time_per_unit_minutes=10.0, status=OperationStatus.PENDING, work_center=sample_work_center
        )
        op3 = WorkOrderOperation(
            id=3, organization_id=1, plant_id=1, work_order_id=1, operation_number=30,
            operation_name="Pack", work_center_id=1, setup_time_minutes=15.0,
            run_time_per_unit_minutes=2.0, status=OperationStatus.PENDING, work_center=sample_work_center
        )

        sample_work_order.operations = [op1, op2, op3]
        sample_work_order.planned_quantity = 10.0

        db_session.query.return_value.filter.return_value.first.return_value = sample_work_order

        # Test: Calculate critical path
        result = scheduling_service.calculate_critical_path(work_order_id=1)

        # Assert: All operations on critical path (sequential chain)
        assert len(result['critical_path_operations']) == 3
        assert result['total_duration'] > 0
        # Total = (30+50)=80 + (45+100)=145 + (15+20)=35 = 260 minutes
        assert result['total_duration'] == 260

    def test_check_capacity_conflicts_detects_overlaps(
        self, scheduling_service, db_session, sample_work_center
    ):
        """Should detect work center overloads in schedule"""
        # Setup: Schedule with overlapping operations on same work center
        from app.domain.entities.schedule import Schedule
        from app.domain.entities.scheduled_operation import ScheduledOperation

        schedule = Schedule(
            id=1, organization_id=1, plant_id=1, schedule_number="SCH-001",
            schedule_name="Daily Schedule", schedule_type="DAILY",
            schedule_date=datetime(2025, 1, 10), status="DRAFT", created_by_user_id=1
        )

        # Two operations overlapping on same work center
        sched_op1 = ScheduledOperation(
            id=1, schedule_id=1, work_order_operation_id=1, work_center_id=1,
            scheduled_start=datetime(2025, 1, 10, 8, 0),
            scheduled_end=datetime(2025, 1, 10, 10, 0),
            predecessor_operation_ids=[], slack_time_minutes=0, is_critical_path=True
        )
        sched_op2 = ScheduledOperation(
            id=2, schedule_id=1, work_order_operation_id=2, work_center_id=1,
            scheduled_start=datetime(2025, 1, 10, 9, 0),  # Overlaps with op1
            scheduled_end=datetime(2025, 1, 10, 11, 0),
            predecessor_operation_ids=[], slack_time_minutes=0, is_critical_path=True
        )

        schedule.scheduled_operations = [sched_op1, sched_op2]

        # Mock the query to return schedule - need to handle query(Schedule)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = schedule
        db_session.query.return_value = mock_query

        # Test: Check for conflicts
        conflicts = scheduling_service.check_capacity_conflicts(schedule_id=1)

        # Assert: Conflict detected on work center 1
        assert len(conflicts) > 0
        assert conflicts[0]['work_center_id'] == 1
        assert len(conflicts[0]['operations']) == 2


class TestSchedulingStrategyService:
    """Test SchedulingStrategyService domain service"""

    @pytest.fixture
    def work_orders(self):
        """Create sample work orders for sorting"""
        return [
            WorkOrder(
                id=1, work_order_number="WO-001", material_id=100,
                end_date_planned=datetime(2025, 1, 20), planned_quantity=10.0,
                order_type=OrderType.PRODUCTION, order_status=OrderStatus.PLANNED,
                priority=5, created_by_user_id=1, organization_id=1, plant_id=1
            ),
            WorkOrder(
                id=2, work_order_number="WO-002", material_id=101,
                end_date_planned=datetime(2025, 1, 15), planned_quantity=5.0,
                order_type=OrderType.PRODUCTION, order_status=OrderStatus.PLANNED,
                priority=5, created_by_user_id=1, organization_id=1, plant_id=1
            ),
            WorkOrder(
                id=3, work_order_number="WO-003", material_id=102,
                end_date_planned=datetime(2025, 1, 25), planned_quantity=8.0,
                order_type=OrderType.PRODUCTION, order_status=OrderStatus.PLANNED,
                priority=5, created_by_user_id=1, organization_id=1, plant_id=1
            )
        ]

    def test_earliest_due_date_sorts_by_due_date(self, work_orders):
        """Should sort work orders by due date (earliest first)"""
        from app.domain.services.scheduling_strategy_service import SchedulingStrategyService

        strategy_service = SchedulingStrategyService()
        sorted_orders = strategy_service.earliest_due_date(work_orders)

        # Assert: Sorted by due date
        assert sorted_orders[0].id == 2  # Jan 15
        assert sorted_orders[1].id == 1  # Jan 20
        assert sorted_orders[2].id == 3  # Jan 25

    def test_shortest_processing_time_sorts_by_quantity(self, work_orders):
        """Should sort work orders by processing time (shortest first)"""
        from app.domain.services.scheduling_strategy_service import SchedulingStrategyService

        # Add operations to calculate processing time
        for wo in work_orders:
            op = WorkOrderOperation(
                id=wo.id, work_order_id=wo.id, operation_number=10,
                operation_name="Op", work_center_id=1,
                setup_time_minutes=30.0, run_time_per_unit_minutes=5.0,
                status=OperationStatus.PENDING, organization_id=1, plant_id=1
            )
            wo.operations = [op]

        strategy_service = SchedulingStrategyService()
        sorted_orders = strategy_service.shortest_processing_time(work_orders)

        # Assert: Sorted by total processing time
        # WO-002: 30 + 5*5 = 55 min
        # WO-003: 30 + 5*8 = 70 min
        # WO-001: 30 + 5*10 = 80 min
        assert sorted_orders[0].id == 2
        assert sorted_orders[1].id == 3
        assert sorted_orders[2].id == 1

    def test_critical_ratio_sorts_urgency(self, work_orders):
        """Should calculate critical ratio and sort by urgency"""
        from app.domain.services.scheduling_strategy_service import SchedulingStrategyService

        # Add operations
        for wo in work_orders:
            op = WorkOrderOperation(
                id=wo.id, work_order_id=wo.id, operation_number=10,
                operation_name="Op", work_center_id=1,
                setup_time_minutes=30.0, run_time_per_unit_minutes=5.0,
                status=OperationStatus.PENDING, organization_id=1, plant_id=1
            )
            wo.operations = [op]

        strategy_service = SchedulingStrategyService()
        current_date = datetime(2025, 1, 10)
        sorted_orders = strategy_service.critical_ratio(work_orders, current_date)

        # Assert: Sorted by critical ratio (most urgent first)
        # WO-002: (Jan 15 - Jan 10) / 55min = 5 days / 0.92 hrs = high CR
        # WO-001: (Jan 20 - Jan 10) / 80min = 10 days / 1.33 hrs = higher CR
        # WO-003: (Jan 25 - Jan 10) / 70min = 15 days / 1.17 hrs = highest CR
        # Lower CR = more urgent
        assert sorted_orders[0].id == 2  # Lowest CR (most urgent)


class TestScheduleEntity:
    """Test Schedule domain entity"""

    def test_schedule_creation(self):
        """Should create schedule entity"""
        from app.domain.entities.schedule import Schedule

        schedule = Schedule(
            id=None,
            organization_id=1,
            plant_id=1,
            schedule_number="SCH-001",
            schedule_name="Daily Production Schedule",
            schedule_type="DAILY",
            schedule_date=datetime(2025, 1, 10),
            status="DRAFT",
            created_by_user_id=1
        )

        assert schedule.schedule_number == "SCH-001"
        assert schedule.status == "DRAFT"

    def test_schedule_publish(self):
        """Should transition schedule from DRAFT to PUBLISHED"""
        from app.domain.entities.schedule import Schedule

        schedule = Schedule(
            id=1, organization_id=1, plant_id=1, schedule_number="SCH-001",
            schedule_name="Schedule", schedule_type="DAILY",
            schedule_date=datetime(2025, 1, 10), status="DRAFT", created_by_user_id=1
        )

        schedule.publish()
        assert schedule.status == "PUBLISHED"

    def test_schedule_activate(self):
        """Should transition schedule from PUBLISHED to ACTIVE"""
        from app.domain.entities.schedule import Schedule

        schedule = Schedule(
            id=1, organization_id=1, plant_id=1, schedule_number="SCH-001",
            schedule_name="Schedule", schedule_type="DAILY",
            schedule_date=datetime(2025, 1, 10), status="PUBLISHED", created_by_user_id=1
        )

        schedule.activate()
        assert schedule.status == "ACTIVE"

    def test_get_gantt_chart_data(self):
        """Should return operations grouped by work center for Gantt chart"""
        from app.domain.entities.schedule import Schedule
        from app.domain.entities.scheduled_operation import ScheduledOperation

        schedule = Schedule(
            id=1, organization_id=1, plant_id=1, schedule_number="SCH-001",
            schedule_name="Schedule", schedule_type="DAILY",
            schedule_date=datetime(2025, 1, 10), status="DRAFT", created_by_user_id=1
        )

        # Add operations on different work centers
        op1 = ScheduledOperation(
            id=1, schedule_id=1, work_order_operation_id=1, work_center_id=1,
            scheduled_start=datetime(2025, 1, 10, 8, 0),
            scheduled_end=datetime(2025, 1, 10, 10, 0),
            predecessor_operation_ids=[], slack_time_minutes=0, is_critical_path=True
        )
        op2 = ScheduledOperation(
            id=2, schedule_id=1, work_order_operation_id=2, work_center_id=2,
            scheduled_start=datetime(2025, 1, 10, 9, 0),
            scheduled_end=datetime(2025, 1, 10, 11, 0),
            predecessor_operation_ids=[], slack_time_minutes=0, is_critical_path=False
        )

        schedule.scheduled_operations = [op1, op2]

        gantt_data = schedule.get_gantt_chart_data()

        assert len(gantt_data) == 2  # 2 work centers
        assert 1 in gantt_data
        assert 2 in gantt_data
        assert len(gantt_data[1]) == 1
        assert len(gantt_data[2]) == 1


class TestScheduledOperationEntity:
    """Test ScheduledOperation domain entity"""

    def test_scheduled_operation_creation(self):
        """Should create scheduled operation"""
        from app.domain.entities.scheduled_operation import ScheduledOperation

        op = ScheduledOperation(
            id=None,
            schedule_id=1,
            work_order_operation_id=1,
            work_center_id=1,
            scheduled_start=datetime(2025, 1, 10, 8, 0),
            scheduled_end=datetime(2025, 1, 10, 10, 0),
            predecessor_operation_ids=[],
            slack_time_minutes=15,
            is_critical_path=False
        )

        assert op.schedule_id == 1
        assert op.slack_time_minutes == 15

    def test_calculate_duration(self):
        """Should calculate duration in minutes"""
        from app.domain.entities.scheduled_operation import ScheduledOperation

        op = ScheduledOperation(
            id=1, schedule_id=1, work_order_operation_id=1, work_center_id=1,
            scheduled_start=datetime(2025, 1, 10, 8, 0),
            scheduled_end=datetime(2025, 1, 10, 10, 30),
            predecessor_operation_ids=[], slack_time_minutes=0, is_critical_path=True
        )

        duration = op.calculate_duration()
        assert duration == 150  # 2.5 hours = 150 minutes

    def test_validate_scheduled_end_after_start(self):
        """Should raise error if scheduled_end before scheduled_start"""
        from app.domain.entities.scheduled_operation import ScheduledOperation

        with pytest.raises(ValueError, match="scheduled_end must be after scheduled_start"):
            ScheduledOperation(
                id=1, schedule_id=1, work_order_operation_id=1, work_center_id=1,
                scheduled_start=datetime(2025, 1, 10, 10, 0),
                scheduled_end=datetime(2025, 1, 10, 8, 0),  # Before start
                predecessor_operation_ids=[], slack_time_minutes=0, is_critical_path=True
            )
