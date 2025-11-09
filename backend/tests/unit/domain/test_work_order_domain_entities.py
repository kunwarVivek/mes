"""
Unit tests for Work Order domain entities with business logic.
Following TDD approach: RED -> GREEN -> REFACTOR
Phase 3: Production Planning Module - Domain Layer
"""
import pytest
from datetime import datetime, timedelta
from app.domain.entities.work_order import (
    WorkOrderDomain,
    WorkOrderOperationDomain,
    WorkCenterDomain
)


class TestWorkCenterDomain:
    """Test WorkCenter domain entity with business logic"""

    def test_create_work_center_domain(self):
        """Test creating a work center domain entity"""
        wc = WorkCenterDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_center_code="WC001",
            work_center_name="Assembly Line 1",
            work_center_type="ASSEMBLY",
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=True
        )

        assert wc.id == 1
        assert wc.work_center_code == "WC001"
        assert wc.work_center_name == "Assembly Line 1"
        assert wc.capacity_per_hour == 10.0
        assert wc.cost_per_hour == 50.0
        assert wc.is_active is True

    def test_capacity_validation_positive(self):
        """Test that capacity_per_hour must be positive"""
        with pytest.raises(ValueError, match="Capacity per hour must be positive"):
            WorkCenterDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_center_code="WC001",
                work_center_name="Assembly Line 1",
                work_center_type="ASSEMBLY",
                capacity_per_hour=0.0,  # Invalid
                cost_per_hour=50.0,
                is_active=True
            )

    def test_cost_validation_non_negative(self):
        """Test that cost_per_hour must be non-negative"""
        with pytest.raises(ValueError, match="Cost per hour cannot be negative"):
            WorkCenterDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_center_code="WC001",
                work_center_name="Assembly Line 1",
                work_center_type="ASSEMBLY",
                capacity_per_hour=10.0,
                cost_per_hour=-5.0,  # Invalid
                is_active=True
            )

    def test_organization_id_validation(self):
        """Test that organization_id must be positive"""
        with pytest.raises(ValueError, match="Organization ID must be positive"):
            WorkCenterDomain(
                id=1,
                organization_id=0,  # Invalid
                plant_id=101,
                work_center_code="WC001",
                work_center_name="Assembly Line 1",
                work_center_type="ASSEMBLY",
                capacity_per_hour=10.0,
                cost_per_hour=50.0,
                is_active=True
            )

    def test_plant_id_validation(self):
        """Test that plant_id must be positive"""
        with pytest.raises(ValueError, match="Plant ID must be positive"):
            WorkCenterDomain(
                id=1,
                organization_id=1,
                plant_id=0,  # Invalid
                work_center_code="WC001",
                work_center_name="Assembly Line 1",
                work_center_type="ASSEMBLY",
                capacity_per_hour=10.0,
                cost_per_hour=50.0,
                is_active=True
            )

    def test_work_center_code_empty(self):
        """Test that work_center_code cannot be empty"""
        with pytest.raises(ValueError, match="Work center code cannot be empty"):
            WorkCenterDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_center_code="",  # Invalid
                work_center_name="Assembly Line 1",
                work_center_type="ASSEMBLY",
                capacity_per_hour=10.0,
                cost_per_hour=50.0,
                is_active=True
            )

    def test_activate_work_center(self):
        """Test activating a work center"""
        wc = WorkCenterDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_center_code="WC001",
            work_center_name="Assembly Line 1",
            work_center_type="ASSEMBLY",
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=False
        )

        assert wc.is_active is False
        wc.activate()
        assert wc.is_active is True

    def test_deactivate_work_center(self):
        """Test deactivating a work center"""
        wc = WorkCenterDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_center_code="WC001",
            work_center_name="Assembly Line 1",
            work_center_type="ASSEMBLY",
            capacity_per_hour=10.0,
            cost_per_hour=50.0,
            is_active=True
        )

        assert wc.is_active is True
        wc.deactivate()
        assert wc.is_active is False


class TestWorkOrderDomain:
    """Test WorkOrder domain entity with business logic"""

    def test_create_work_order_domain(self):
        """Test creating a work order domain entity"""
        wo = WorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=1,
            order_type="PRODUCTION",
            order_status="PLANNED",
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )

        assert wo.id == 1
        assert wo.work_order_number == "WO2024-001"
        assert wo.order_status == "PLANNED"
        assert wo.planned_quantity == 100.0
        assert wo.priority == 5

    def test_planned_quantity_validation_positive(self):
        """Test that planned_quantity must be positive"""
        with pytest.raises(ValueError, match="Planned quantity must be positive"):
            WorkOrderDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_order_number="WO2024-001",
                material_id=1,
                order_type="PRODUCTION",
                order_status="PLANNED",
                planned_quantity=0.0,  # Invalid
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=5),
                priority=5,
                created_by_user_id=1
            )

    def test_actual_quantity_validation_non_negative(self):
        """Test that actual_quantity must be non-negative"""
        with pytest.raises(ValueError, match="Actual quantity cannot be negative"):
            WorkOrderDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_order_number="WO2024-001",
                material_id=1,
                order_type="PRODUCTION",
                order_status="PLANNED",
                planned_quantity=100.0,
                actual_quantity=-5.0,  # Invalid
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=5),
                priority=5,
                created_by_user_id=1
            )

    def test_actual_quantity_not_exceed_planned(self):
        """Test that actual_quantity cannot exceed planned_quantity"""
        with pytest.raises(ValueError, match="Actual quantity cannot exceed planned quantity"):
            WorkOrderDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_order_number="WO2024-001",
                material_id=1,
                order_type="PRODUCTION",
                order_status="PLANNED",
                planned_quantity=100.0,
                actual_quantity=150.0,  # Invalid
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=5),
                priority=5,
                created_by_user_id=1
            )

    def test_priority_range_validation(self):
        """Test that priority must be between 1 and 10"""
        # Test priority < 1
        with pytest.raises(ValueError, match="Priority must be between 1 and 10"):
            WorkOrderDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_order_number="WO2024-001",
                material_id=1,
                order_type="PRODUCTION",
                order_status="PLANNED",
                planned_quantity=100.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=5),
                priority=0,  # Invalid
                created_by_user_id=1
            )

        # Test priority > 10
        with pytest.raises(ValueError, match="Priority must be between 1 and 10"):
            WorkOrderDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_order_number="WO2024-001",
                material_id=1,
                order_type="PRODUCTION",
                order_status="PLANNED",
                planned_quantity=100.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=5),
                priority=11,  # Invalid
                created_by_user_id=1
            )

    def test_date_validation_start_before_end(self):
        """Test that start_date must be before end_date"""
        end_date = datetime.now()
        start_date = end_date + timedelta(days=5)  # Start after end

        with pytest.raises(ValueError, match="Start date must be before end date"):
            WorkOrderDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_order_number="WO2024-001",
                material_id=1,
                order_type="PRODUCTION",
                order_status="PLANNED",
                planned_quantity=100.0,
                actual_quantity=0.0,
                start_date_planned=start_date,
                end_date_planned=end_date,
                priority=5,
                created_by_user_id=1
            )

    def test_start_work_order(self):
        """Test starting a work order (RELEASED -> IN_PROGRESS)"""
        wo = WorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=1,
            order_type="PRODUCTION",
            order_status="RELEASED",
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )

        assert wo.order_status == "RELEASED"
        wo.start()
        assert wo.order_status == "IN_PROGRESS"
        assert wo.start_date_actual is not None

    def test_start_work_order_invalid_status(self):
        """Test that work order can only be started from RELEASED status"""
        wo = WorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=1,
            order_type="PRODUCTION",
            order_status="PLANNED",  # Not RELEASED
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )

        with pytest.raises(ValueError, match="Work order can only be started from RELEASED status"):
            wo.start()

    def test_complete_work_order(self):
        """Test completing a work order (IN_PROGRESS -> COMPLETED)"""
        wo = WorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=1,
            order_type="PRODUCTION",
            order_status="IN_PROGRESS",
            planned_quantity=100.0,
            actual_quantity=100.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )

        assert wo.order_status == "IN_PROGRESS"
        wo.complete()
        assert wo.order_status == "COMPLETED"
        assert wo.end_date_actual is not None

    def test_complete_work_order_invalid_status(self):
        """Test that work order can only be completed from IN_PROGRESS status"""
        wo = WorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=1,
            order_type="PRODUCTION",
            order_status="PLANNED",  # Not IN_PROGRESS
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )

        with pytest.raises(ValueError, match="Work order can only be completed from IN_PROGRESS status"):
            wo.complete()

    def test_cancel_work_order(self):
        """Test cancelling a work order"""
        wo = WorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=1,
            order_type="PRODUCTION",
            order_status="PLANNED",
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )

        assert wo.order_status == "PLANNED"
        wo.cancel()
        assert wo.order_status == "CANCELLED"

    def test_cancel_completed_work_order(self):
        """Test that completed work order cannot be cancelled"""
        wo = WorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=1,
            order_type="PRODUCTION",
            order_status="COMPLETED",
            planned_quantity=100.0,
            actual_quantity=100.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )

        with pytest.raises(ValueError, match="Cannot cancel a completed work order"):
            wo.cancel()

    def test_update_actual_quantity(self):
        """Test updating actual quantity"""
        wo = WorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=1,
            order_type="PRODUCTION",
            order_status="IN_PROGRESS",
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )

        wo.update_actual_quantity(50.0)
        assert wo.actual_quantity == 50.0

    def test_update_actual_quantity_exceeds_planned(self):
        """Test that actual quantity cannot exceed planned quantity"""
        wo = WorkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="WO2024-001",
            material_id=1,
            order_type="PRODUCTION",
            order_status="IN_PROGRESS",
            planned_quantity=100.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=5),
            priority=5,
            created_by_user_id=1
        )

        with pytest.raises(ValueError, match="Actual quantity cannot exceed planned quantity"):
            wo.update_actual_quantity(150.0)


class TestWorkOrderOperationDomain:
    """Test WorkOrderOperation domain entity with business logic"""

    def test_create_operation_domain(self):
        """Test creating a work order operation domain entity"""
        op = WorkOrderOperationDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_id=1,
            operation_number=10,
            operation_name="Assembly",
            work_center_id=1,
            setup_time_minutes=30.0,
            run_time_per_unit_minutes=5.0,
            status="PENDING"
        )

        assert op.id == 1
        assert op.operation_number == 10
        assert op.operation_name == "Assembly"
        assert op.setup_time_minutes == 30.0
        assert op.status == "PENDING"

    def test_operation_number_validation(self):
        """Test that operation_number must be positive"""
        with pytest.raises(ValueError, match="Operation number must be positive"):
            WorkOrderOperationDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_order_id=1,
                operation_number=0,  # Invalid
                operation_name="Assembly",
                work_center_id=1,
                setup_time_minutes=30.0,
                run_time_per_unit_minutes=5.0,
                status="PENDING"
            )

    def test_setup_time_validation(self):
        """Test that setup_time_minutes must be non-negative"""
        with pytest.raises(ValueError, match="Setup time cannot be negative"):
            WorkOrderOperationDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_order_id=1,
                operation_number=10,
                operation_name="Assembly",
                work_center_id=1,
                setup_time_minutes=-5.0,  # Invalid
                run_time_per_unit_minutes=5.0,
                status="PENDING"
            )

    def test_run_time_validation(self):
        """Test that run_time_per_unit_minutes must be non-negative"""
        with pytest.raises(ValueError, match="Run time per unit cannot be negative"):
            WorkOrderOperationDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                work_order_id=1,
                operation_number=10,
                operation_name="Assembly",
                work_center_id=1,
                setup_time_minutes=30.0,
                run_time_per_unit_minutes=-2.0,  # Invalid
                status="PENDING"
            )
