"""
Unit tests for Rework Service with business logic.
Following TDD approach: RED -> GREEN -> REFACTOR
Phase 3: Production Planning Module - Rework Order Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from app.application.services.rework_service import ReworkService
from app.domain.entities.rework_order import ReworkOrderDomain, ReworkMode
from app.models.work_order import ReworkConfig


class TestReworkService:
    """Test ReworkService business operations"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def rework_service(self, mock_db):
        """Create ReworkService instance with mocked dependencies"""
        return ReworkService(db=mock_db)

    def test_create_rework_order_with_consume_additional_materials(self, rework_service, mock_db):
        """Test creating rework order with CONSUME_ADDITIONAL_MATERIALS mode"""
        # Arrange
        parent_work_order = Mock()
        parent_work_order.id = 100
        parent_work_order.material_id = 1
        parent_work_order.organization_id = 1
        parent_work_order.plant_id = 101
        parent_work_order.order_status = "IN_PROGRESS"

        mock_db.query().filter().first.return_value = parent_work_order

        rework_data = {
            "work_order_number": "RW2024-001",
            "planned_quantity": 50.0,
            "parent_work_order_id": 100,
            "rework_reason_code": "DEFECT_001",
            "rework_mode": ReworkMode.CONSUME_ADDITIONAL_MATERIALS,
            "priority": 8,
            "created_by_user_id": 1
        }

        # Act
        rework_order = rework_service.create_rework_order(**rework_data)

        # Assert
        assert rework_order is not None
        assert rework_order.is_rework_order is True
        assert rework_order.parent_work_order_id == 100
        assert rework_order.rework_mode == ReworkMode.CONSUME_ADDITIONAL_MATERIALS

    def test_create_rework_order_validates_parent_exists(self, rework_service, mock_db):
        """Test that rework order creation validates parent work order exists"""
        # Arrange
        mock_db.query().filter().first.return_value = None  # Parent doesn't exist

        rework_data = {
            "work_order_number": "RW2024-002",
            "planned_quantity": 50.0,
            "parent_work_order_id": 999,  # Non-existent parent
            "rework_reason_code": "DEFECT_001",
            "rework_mode": ReworkMode.CONSUME_ADDITIONAL_MATERIALS,
            "priority": 8,
            "created_by_user_id": 1
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Parent work order not found"):
            rework_service.create_rework_order(**rework_data)

    def test_create_rework_order_validates_parent_not_cancelled(self, rework_service, mock_db):
        """Test that rework order cannot be created for cancelled parent"""
        # Arrange
        parent_work_order = Mock()
        parent_work_order.id = 100
        parent_work_order.order_status = "CANCELLED"

        mock_db.query().filter().first.return_value = parent_work_order

        rework_data = {
            "work_order_number": "RW2024-003",
            "planned_quantity": 50.0,
            "parent_work_order_id": 100,
            "rework_reason_code": "DEFECT_001",
            "rework_mode": ReworkMode.CONSUME_ADDITIONAL_MATERIALS,
            "priority": 8,
            "created_by_user_id": 1
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot create rework order for cancelled work order"):
            rework_service.create_rework_order(**rework_data)

    def test_get_rework_config_for_organization(self, rework_service, mock_db):
        """Test getting rework configuration for organization/plant"""
        # Arrange
        mock_config = Mock(spec=ReworkConfig)
        mock_config.organization_id = 1
        mock_config.plant_id = 101
        mock_config.default_rework_mode = ReworkMode.CONSUME_ADDITIONAL_MATERIALS
        mock_config.require_reason_code = True
        mock_config.allow_multiple_rework_cycles = True

        mock_db.query().filter().first.return_value = mock_config

        # Act
        config = rework_service.get_rework_config(organization_id=1, plant_id=101)

        # Assert
        assert config is not None
        assert config.organization_id == 1
        assert config.plant_id == 101
        assert config.default_rework_mode == ReworkMode.CONSUME_ADDITIONAL_MATERIALS
        assert config.require_reason_code is True

    def test_validate_rework_config_requires_reason_code(self, rework_service, mock_db):
        """Test that rework config can enforce reason code requirement"""
        # Arrange
        mock_config = Mock(spec=ReworkConfig)
        mock_config.require_reason_code = True

        mock_db.query().filter().first.return_value = mock_config

        # Act & Assert
        result = rework_service.validate_rework_config(
            organization_id=1,
            plant_id=101,
            reason_code=None
        )

        assert result is False

    def test_validate_multiple_rework_cycles_allowed(self, rework_service, mock_db):
        """Test that config can control multiple rework cycles"""
        # Arrange - Config allows multiple cycles
        mock_config = Mock(spec=ReworkConfig)
        mock_config.allow_multiple_rework_cycles = True

        mock_db.query().filter().first.return_value = mock_config

        # Act
        result = rework_service.can_create_rework_cycle(
            organization_id=1,
            plant_id=101,
            current_cycle=2
        )

        # Assert
        assert result is True

    def test_validate_multiple_rework_cycles_blocked(self, rework_service, mock_db):
        """Test that config can block multiple rework cycles"""
        # Arrange - Config blocks multiple cycles
        mock_config = Mock(spec=ReworkConfig)
        mock_config.allow_multiple_rework_cycles = False

        mock_db.query().filter().first.return_value = mock_config

        # Act
        result = rework_service.can_create_rework_cycle(
            organization_id=1,
            plant_id=101,
            current_cycle=2
        )

        # Assert
        assert result is False

    def test_calculate_rework_material_consumption_consume_mode(self, rework_service, mock_db):
        """Test material consumption calculation for CONSUME_ADDITIONAL_MATERIALS mode"""
        # Arrange
        rework_order = Mock()
        rework_order.rework_mode = ReworkMode.CONSUME_ADDITIONAL_MATERIALS
        rework_order.planned_quantity = 50.0

        bom_materials = [
            Mock(material_id=1, quantity_per_unit=2.0),
            Mock(material_id=2, quantity_per_unit=1.5)
        ]

        # Act
        material_requirements = rework_service.calculate_material_requirements(
            rework_order=rework_order,
            bom_materials=bom_materials
        )

        # Assert
        assert len(material_requirements) == 2
        assert material_requirements[0]["material_id"] == 1
        assert material_requirements[0]["planned_quantity"] == 100.0  # 50 * 2.0
        assert material_requirements[1]["material_id"] == 2
        assert material_requirements[1]["planned_quantity"] == 75.0   # 50 * 1.5

    def test_calculate_rework_material_consumption_reprocess_mode(self, rework_service, mock_db):
        """Test material consumption calculation for REPROCESS_EXISTING_WIP mode"""
        # Arrange
        rework_order = Mock()
        rework_order.rework_mode = ReworkMode.REPROCESS_EXISTING_WIP
        rework_order.planned_quantity = 50.0

        bom_materials = [
            Mock(material_id=1, quantity_per_unit=2.0),
            Mock(material_id=2, quantity_per_unit=1.5)
        ]

        # Act
        material_requirements = rework_service.calculate_material_requirements(
            rework_order=rework_order,
            bom_materials=bom_materials
        )

        # Assert
        # REPROCESS_EXISTING_WIP should not consume additional materials
        assert len(material_requirements) == 0

    def test_track_rework_cost_additional_materials(self, rework_service, mock_db):
        """Test cost tracking for rework with additional materials"""
        # Arrange
        rework_order = Mock()
        rework_order.id = 1
        rework_order.rework_mode = ReworkMode.CONSUME_ADDITIONAL_MATERIALS

        material_costs = [
            {"material_id": 1, "quantity": 100.0, "unit_cost": 5.0},
            {"material_id": 2, "quantity": 75.0, "unit_cost": 3.0}
        ]

        labor_hours = 10.0
        labor_rate = 25.0

        # Act
        total_cost = rework_service.calculate_rework_cost(
            rework_order=rework_order,
            material_costs=material_costs,
            labor_hours=labor_hours,
            labor_rate=labor_rate
        )

        # Assert
        # Material cost: (100 * 5) + (75 * 3) = 500 + 225 = 725
        # Labor cost: 10 * 25 = 250
        # Total: 725 + 250 = 975
        assert total_cost == 975.0

    def test_link_rework_to_parent(self, rework_service, mock_db):
        """Test linking rework order to parent work order"""
        # Arrange
        parent_work_order = Mock()
        parent_work_order.id = 100

        rework_order = Mock()
        rework_order.id = 200
        rework_order.parent_work_order_id = 100

        # Act
        rework_service.link_rework_to_parent(
            rework_order_id=200,
            parent_work_order_id=100
        )

        # Assert
        # Verify the relationship was created
        mock_db.commit.assert_called()
