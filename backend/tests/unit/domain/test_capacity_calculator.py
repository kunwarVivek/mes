"""
Unit tests for CapacityCalculator domain service.
Phase 3: Production Planning Module - Component 3
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.services.capacity_calculator import CapacityCalculator
from app.models.work_order import WorkCenter, WorkCenterType, WorkOrder, WorkOrderOperation, OrderStatus, OrderType, OperationStatus
from app.models.material import Material, UnitOfMeasure, MaterialCategory, ProcurementType, MRPType, DimensionType


class TestCapacityCalculator:
    """Test suite for CapacityCalculator domain service"""

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
        """Setup test data for capacity calculator tests"""
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

        # Create category
        category = MaterialCategory(
            id=1,
            organization_id=1,
            category_code="PROD",
            category_name="Products",
            is_active=True
        )
        db_session.add(category)

        # Create material
        material = Material(
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
        db_session.add(material)

        # Create work center with 8 hours/day capacity
        work_center = WorkCenter(
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
        db_session.add(work_center)

        db_session.commit()

        return {
            'work_center': work_center,
            'material': material
        }

    def test_calculate_work_center_load_no_operations(self, db_session, setup_test_data):
        """Test capacity calculation when work center has no operations"""
        calculator = CapacityCalculator(db_session)

        start_date = datetime(2025, 11, 1)
        end_date = datetime(2025, 11, 30)

        result = calculator.calculate_work_center_load(
            work_center_id=1,
            start_date=start_date,
            end_date=end_date
        )

        assert result is not None
        assert result['total_hours'] == 0.0
        assert result['capacity_hours'] > 0.0  # Should have capacity available
        assert result['utilization_pct'] == 0.0
        assert result['available_hours'] > 0.0

    def test_calculate_work_center_load_with_operations(self, db_session, setup_test_data):
        """Test capacity calculation with some operations scheduled"""
        calculator = CapacityCalculator(db_session)

        # Create work order
        work_order = WorkOrder(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-001",
            material_id=1,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            end_date_planned=datetime(2025, 11, 15),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        # Add operation: setup 1 hour + 100 units * 3 min = 6 hours total
        operation = WorkOrderOperation(
            organization_id=1,
            plant_id=1,
            work_order_id=1,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=1,
            setup_time_minutes=60.0,
            run_time_per_unit_minutes=3.0,
            status=OperationStatus.PENDING,
            start_time=datetime(2025, 11, 10),
            end_time=datetime(2025, 11, 10, 6, 0)
        )
        db_session.add(operation)
        db_session.commit()

        start_date = datetime(2025, 11, 1)
        end_date = datetime(2025, 11, 30)

        result = calculator.calculate_work_center_load(
            work_center_id=1,
            start_date=start_date,
            end_date=end_date
        )

        assert result is not None
        assert result['total_hours'] == 6.0  # 1 hour setup + 5 hours run
        assert result['utilization_pct'] > 0.0
        assert result['utilization_pct'] < 100.0  # Should be less than 100%

    def test_calculate_work_center_load_fully_loaded(self, db_session, setup_test_data):
        """Test capacity calculation when work center is fully loaded (100%)"""
        calculator = CapacityCalculator(db_session)

        # Create work order
        work_order = WorkOrder(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-001",
            material_id=1,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=1000.0,
            actual_quantity=0.0,
            end_date_planned=datetime(2025, 11, 15),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        # Calculate capacity hours for November (30 days * 8 hours = 240 hours)
        # Add operation to consume all capacity
        operation = WorkOrderOperation(
            organization_id=1,
            plant_id=1,
            work_order_id=1,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=1,
            setup_time_minutes=0.0,
            run_time_per_unit_minutes=14.4,  # 14.4 min/unit * 1000 = 14400 min = 240 hours
            status=OperationStatus.PENDING,
            start_time=datetime(2025, 11, 1),
            end_time=datetime(2025, 11, 30)
        )
        db_session.add(operation)
        db_session.commit()

        start_date = datetime(2025, 11, 1)
        end_date = datetime(2025, 11, 30)

        result = calculator.calculate_work_center_load(
            work_center_id=1,
            start_date=start_date,
            end_date=end_date
        )

        assert result is not None
        assert result['total_hours'] == 240.0
        assert result['utilization_pct'] == 100.0
        assert result['available_hours'] == 0.0

    def test_calculate_work_center_load_overloaded(self, db_session, setup_test_data):
        """Test capacity calculation when work center is overloaded (>100%)"""
        calculator = CapacityCalculator(db_session)

        # Create work orders
        work_order_1 = WorkOrder(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-001",
            material_id=1,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=1000.0,
            actual_quantity=0.0,
            end_date_planned=datetime(2025, 11, 15),
            priority=5,
            created_by_user_id=1
        )
        work_order_2 = WorkOrder(
            id=2,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-002",
            material_id=1,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=500.0,
            actual_quantity=0.0,
            end_date_planned=datetime(2025, 11, 20),
            priority=5,
            created_by_user_id=1
        )
        db_session.add_all([work_order_1, work_order_2])
        db_session.commit()

        # Add operations that exceed capacity
        # Total: 240 + 120 = 360 hours in 240-hour capacity period
        operation_1 = WorkOrderOperation(
            organization_id=1,
            plant_id=1,
            work_order_id=1,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=1,
            setup_time_minutes=0.0,
            run_time_per_unit_minutes=14.4,  # 240 hours
            status=OperationStatus.PENDING,
            start_time=datetime(2025, 11, 1),
            end_time=datetime(2025, 11, 30)
        )
        operation_2 = WorkOrderOperation(
            organization_id=1,
            plant_id=1,
            work_order_id=2,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=1,
            setup_time_minutes=0.0,
            run_time_per_unit_minutes=14.4,  # 120 hours
            status=OperationStatus.PENDING,
            start_time=datetime(2025, 11, 1),
            end_time=datetime(2025, 11, 30)
        )
        db_session.add_all([operation_1, operation_2])
        db_session.commit()

        start_date = datetime(2025, 11, 1)
        end_date = datetime(2025, 11, 30)

        result = calculator.calculate_work_center_load(
            work_center_id=1,
            start_date=start_date,
            end_date=end_date
        )

        assert result is not None
        assert result['total_hours'] == 360.0
        assert result['utilization_pct'] > 100.0  # Overloaded
        assert result['utilization_pct'] == 150.0  # 360 / 240 = 150%

    def test_find_available_time_slot_immediate_availability(self, db_session, setup_test_data):
        """Test finding time slot when work center is immediately available"""
        calculator = CapacityCalculator(db_session)

        earliest_start = datetime(2025, 11, 1, 8, 0)
        hours_needed = 4.0

        result = calculator.find_available_time_slot(
            work_center_id=1,
            hours_needed=hours_needed,
            earliest_start=earliest_start
        )

        assert result is not None
        assert result >= earliest_start

    def test_find_available_time_slot_scheduled_after_load(self, db_session, setup_test_data):
        """Test finding time slot after existing workload"""
        calculator = CapacityCalculator(db_session)

        # Create work order with operation occupying Nov 1-5
        work_order = WorkOrder(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-001",
            material_id=1,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            end_date_planned=datetime(2025, 11, 15),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        # Operation consuming 40 hours (5 days * 8 hours)
        operation = WorkOrderOperation(
            organization_id=1,
            plant_id=1,
            work_order_id=1,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=1,
            setup_time_minutes=0.0,
            run_time_per_unit_minutes=24.0,  # 40 hours total
            status=OperationStatus.PENDING,
            start_time=datetime(2025, 11, 1, 8, 0),
            end_time=datetime(2025, 11, 5, 16, 0)
        )
        db_session.add(operation)
        db_session.commit()

        # Try to find slot for 8 hours starting Nov 1
        earliest_start = datetime(2025, 11, 1, 8, 0)
        hours_needed = 8.0

        result = calculator.find_available_time_slot(
            work_center_id=1,
            hours_needed=hours_needed,
            earliest_start=earliest_start
        )

        assert result is not None
        # Should be scheduled after Nov 5 16:00 (when operation ends)
        assert result >= datetime(2025, 11, 5, 16, 0)

    def test_find_available_time_slot_no_availability_error(self, db_session, setup_test_data):
        """Test error when no time slot available within search window"""
        calculator = CapacityCalculator(db_session)

        # Create work order
        work_order = WorkOrder(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_number="WO-001",
            material_id=1,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=100.0,
            actual_quantity=0.0,
            end_date_planned=datetime(2025, 12, 31),
            priority=5,
            created_by_user_id=1
        )
        db_session.add(work_order)
        db_session.commit()

        # Add operation that fills the search window (Nov 1-8 continuously)
        operation = WorkOrderOperation(
            organization_id=1,
            plant_id=1,
            work_order_id=1,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=1,
            setup_time_minutes=0.0,
            run_time_per_unit_minutes=50.0,  # Long runtime
            status=OperationStatus.PENDING,
            start_time=datetime(2025, 11, 1, 8, 0),
            end_time=datetime(2025, 11, 10, 16, 0)  # Goes beyond 7-day window
        )
        db_session.add(operation)
        db_session.commit()

        # Try to find slot with short search window - should raise error
        # Operation runs Nov 1-10, but we only search 7 days
        earliest_start = datetime(2025, 11, 1, 8, 0)
        hours_needed = 8.0

        with pytest.raises(ValueError, match="No available time slot found"):
            calculator.find_available_time_slot(
                work_center_id=1,
                hours_needed=hours_needed,
                earliest_start=earliest_start,
                max_search_days=7  # Operation ends on day 10, beyond our search window
            )
