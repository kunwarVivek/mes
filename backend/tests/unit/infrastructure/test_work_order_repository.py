"""
Unit tests for WorkOrderRepository.
Phase 3 Component 5: Work Order Repository

Tests use mocked database sessions following MaterialRepository test pattern.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.infrastructure.repositories.work_order_repository import WorkOrderRepository
from app.models.work_order import WorkOrder, WorkOrderOperation, WorkOrderMaterial
from app.models.work_order import OrderType, OrderStatus, OperationStatus
from app.models.material import Material


class TestWorkOrderRepositoryCreate:
    """Tests for WorkOrderRepository.create()"""

    def test_create_work_order_success(self):
        """Test successful work order creation"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        work_order_data = {
            "organization_id": 1,
            "plant_id": 1,
            "work_order_number": "WO001",
            "material_id": 1,
            "order_type": "PRODUCTION",
            "order_status": "PLANNED",
            "planned_quantity": 100.0,
            "actual_quantity": 0.0,
            "priority": 5,
            "created_by_user_id": 1
        }

        mock_work_order = WorkOrder(**work_order_data)
        mock_work_order.id = 1
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock()

        # Act
        result = repository.create(work_order_data)

        # Assert
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()
        assert result is not None

    def test_create_work_order_validation_failure(self):
        """Test that create fails with invalid data"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        work_order_data = {
            "organization_id": 0,  # Invalid - must be positive
            "plant_id": 1,
            "work_order_number": "WO001",
            "material_id": 1,
            "order_type": "PRODUCTION",
            "order_status": "PLANNED",
            "planned_quantity": 100.0,
            "actual_quantity": 0.0,
            "priority": 5,
            "created_by_user_id": 1
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Organization ID must be positive"):
            repository.create(work_order_data)

    def test_create_work_order_duplicate_number(self):
        """Test that create fails when work order number exists"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        work_order_data = {
            "organization_id": 1,
            "plant_id": 1,
            "work_order_number": "WO001",
            "material_id": 1,
            "order_type": "PRODUCTION",
            "order_status": "PLANNED",
            "planned_quantity": 100.0,
            "actual_quantity": 0.0,
            "priority": 5,
            "created_by_user_id": 1
        }

        db_session.add = Mock()
        db_session.commit = Mock(side_effect=IntegrityError("", "", ""))
        db_session.rollback = Mock()

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            repository.create(work_order_data)


class TestWorkOrderRepositoryGet:
    """Tests for WorkOrderRepository.get_by_id()"""

    def test_get_by_id_success(self):
        """Test successful retrieval by ID"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_work_order = Mock(spec=WorkOrder)
        mock_work_order.id = 1
        mock_work_order.work_order_number = "WO001"

        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_work_order)

        db_session.query = Mock(return_value=mock_query)

        # Act
        result = repository.get_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1

    def test_get_by_id_not_found(self):
        """Test returns None when ID doesn't exist"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)

        db_session.query = Mock(return_value=mock_query)

        # Act
        result = repository.get_by_id(99999)

        # Assert
        assert result is None


class TestWorkOrderRepositoryStateTransitions:
    """Tests for state transition methods"""

    def test_release_work_order_success(self):
        """Test releasing work order (PLANNED -> RELEASED)"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_work_order = Mock(spec=WorkOrder)
        mock_work_order.id = 1
        mock_work_order.order_status = OrderStatus.PLANNED

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_work_order)

        db_session.query = Mock(return_value=mock_query)
        db_session.commit = Mock()
        db_session.refresh = Mock()

        # Act
        result = repository.release(1)

        # Assert
        assert mock_work_order.order_status == OrderStatus.RELEASED
        db_session.commit.assert_called_once()

    def test_release_work_order_invalid_state(self):
        """Test release fails from non-PLANNED status"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_work_order = Mock(spec=WorkOrder)
        mock_work_order.id = 1
        mock_work_order.order_status = OrderStatus.IN_PROGRESS  # Not PLANNED

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_work_order)

        db_session.query = Mock(return_value=mock_query)

        # Act & Assert
        with pytest.raises(ValueError, match="can only be released from PLANNED status"):
            repository.release(1)

    def test_start_work_order_success(self):
        """Test starting work order (RELEASED -> IN_PROGRESS)"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_work_order = Mock(spec=WorkOrder)
        mock_work_order.id = 1
        mock_work_order.order_status = OrderStatus.RELEASED

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_work_order)

        db_session.query = Mock(return_value=mock_query)
        db_session.commit = Mock()
        db_session.refresh = Mock()

        # Act
        result = repository.start(1)

        # Assert
        assert mock_work_order.order_status == OrderStatus.IN_PROGRESS
        assert mock_work_order.start_date_actual is not None
        db_session.commit.assert_called_once()

    def test_complete_work_order_success(self):
        """Test completing work order (IN_PROGRESS -> COMPLETED)"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_work_order = Mock(spec=WorkOrder)
        mock_work_order.id = 1
        mock_work_order.order_status = OrderStatus.IN_PROGRESS

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_work_order)

        db_session.query = Mock(return_value=mock_query)
        db_session.commit = Mock()
        db_session.refresh = Mock()

        # Act
        result = repository.complete(1)

        # Assert
        assert mock_work_order.order_status == OrderStatus.COMPLETED
        assert mock_work_order.end_date_actual is not None
        db_session.commit.assert_called_once()

    def test_cancel_work_order_success(self):
        """Test cancelling work order (soft delete)"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_work_order = Mock(spec=WorkOrder)
        mock_work_order.id = 1
        mock_work_order.order_status = OrderStatus.PLANNED

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_work_order)

        db_session.query = Mock(return_value=mock_query)
        db_session.commit = Mock()

        # Act
        result = repository.cancel(1)

        # Assert
        assert result is True
        assert mock_work_order.order_status == OrderStatus.CANCELLED
        db_session.commit.assert_called_once()

    def test_cancel_work_order_already_cancelled(self):
        """Test cancel fails when already cancelled"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_work_order = Mock(spec=WorkOrder)
        mock_work_order.id = 1
        mock_work_order.order_status = OrderStatus.CANCELLED

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_work_order)

        db_session.query = Mock(return_value=mock_query)

        # Act & Assert
        with pytest.raises(ValueError, match="already cancelled"):
            repository.cancel(1)


class TestWorkOrderRepositoryUpdate:
    """Tests for WorkOrderRepository.update()"""

    def test_update_work_order_success(self):
        """Test successful work order update"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_work_order = Mock(spec=WorkOrder)
        mock_work_order.id = 1
        mock_work_order.priority = 5
        mock_work_order.planned_quantity = 100.0

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_work_order)

        db_session.query = Mock(return_value=mock_query)
        db_session.commit = Mock()
        db_session.refresh = Mock()

        # Act
        result = repository.update(1, {"priority": 8, "planned_quantity": 150.0})

        # Assert
        assert mock_work_order.priority == 8
        assert mock_work_order.planned_quantity == 150.0
        db_session.commit.assert_called_once()

    def test_update_work_order_not_found(self):
        """Test update raises error when work order not found"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)

        db_session.query = Mock(return_value=mock_query)

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            repository.update(99999, {"priority": 7})


class TestWorkOrderRepositoryList:
    """Tests for WorkOrderRepository.list_by_organization()"""

    def test_list_by_organization_success(self):
        """Test listing work orders with pagination"""
        # Arrange
        db_session = Mock(spec=Session)
        repository = WorkOrderRepository(db_session)

        mock_work_orders = [Mock(spec=WorkOrder) for _ in range(5)]

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=5)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=mock_work_orders[:2])

        db_session.query = Mock(return_value=mock_query)

        # Act
        result = repository.list_by_organization(org_id=1, plant_id=1, page=1, page_size=2)

        # Assert
        assert result["page"] == 1
        assert result["page_size"] == 2
        assert len(result["items"]) == 2
        assert result["total"] == 5
        assert result["total_pages"] == 3
