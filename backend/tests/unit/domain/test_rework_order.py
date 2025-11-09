"""
Unit tests for Rework Order domain entities with business logic.
Following TDD approach: RED -> GREEN -> REFACTOR
Phase 3: Production Planning Module - Rework Order Extension
"""
import pytest
from datetime import datetime, timedelta
from app.domain.entities.rework_order import (
    ReworkOrderDomain,
    ReworkMode
)


class TestReworkOrderDomain:
    """Test ReworkOrder domain entity with business logic"""

    def test_create_rework_order_consume_additional_materials(self):
        """Test creating a rework order with CONSUME_ADDITIONAL_MATERIALS mode"""
        rework_order = ReworkOrderDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            work_order_number="RW2024-001",
            material_id=1,
            order_type="REWORK",
            order_status="PLANNED",
            planned_quantity=50.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=3),
            priority=8,
            created_by_user_id=1,
            is_rework_order=True,
            parent_work_order_id=100,
            rework_reason_code="DEFECT_001",
            rework_mode=ReworkMode.CONSUME_ADDITIONAL_MATERIALS
        )

        assert rework_order.id == 1
        assert rework_order.work_order_number == "RW2024-001"
        assert rework_order.is_rework_order is True
        assert rework_order.parent_work_order_id == 100
        assert rework_order.rework_reason_code == "DEFECT_001"
        assert rework_order.rework_mode == ReworkMode.CONSUME_ADDITIONAL_MATERIALS
        assert rework_order.order_type == "REWORK"

    def test_create_rework_order_reprocess_existing_wip(self):
        """Test creating a rework order with REPROCESS_EXISTING_WIP mode"""
        rework_order = ReworkOrderDomain(
            id=2,
            organization_id=1,
            plant_id=101,
            work_order_number="RW2024-002",
            material_id=1,
            order_type="REWORK",
            order_status="PLANNED",
            planned_quantity=30.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=2),
            priority=9,
            created_by_user_id=1,
            is_rework_order=True,
            parent_work_order_id=101,
            rework_reason_code="QUALITY_002",
            rework_mode=ReworkMode.REPROCESS_EXISTING_WIP
        )

        assert rework_order.rework_mode == ReworkMode.REPROCESS_EXISTING_WIP
        assert rework_order.parent_work_order_id == 101

    def test_create_rework_order_hybrid_mode(self):
        """Test creating a rework order with HYBRID mode"""
        rework_order = ReworkOrderDomain(
            id=3,
            organization_id=1,
            plant_id=101,
            work_order_number="RW2024-003",
            material_id=1,
            order_type="REWORK",
            order_status="PLANNED",
            planned_quantity=20.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=2),
            priority=7,
            created_by_user_id=1,
            is_rework_order=True,
            parent_work_order_id=102,
            rework_reason_code="HYBRID_003",
            rework_mode=ReworkMode.HYBRID
        )

        assert rework_order.rework_mode == ReworkMode.HYBRID

    def test_rework_order_requires_parent_work_order_id(self):
        """Test that rework order must have parent_work_order_id"""
        with pytest.raises(ValueError, match="Rework order must have a parent work order"):
            ReworkOrderDomain(
                id=4,
                organization_id=1,
                plant_id=101,
                work_order_number="RW2024-004",
                material_id=1,
                order_type="REWORK",
                order_status="PLANNED",
                planned_quantity=50.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=3),
                priority=8,
                created_by_user_id=1,
                is_rework_order=True,
                parent_work_order_id=None,  # Invalid - missing parent
                rework_reason_code="DEFECT_001",
                rework_mode=ReworkMode.CONSUME_ADDITIONAL_MATERIALS
            )

    def test_rework_order_requires_reason_code(self):
        """Test that rework order must have reason code"""
        with pytest.raises(ValueError, match="Rework order must have a reason code"):
            ReworkOrderDomain(
                id=5,
                organization_id=1,
                plant_id=101,
                work_order_number="RW2024-005",
                material_id=1,
                order_type="REWORK",
                order_status="PLANNED",
                planned_quantity=50.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=3),
                priority=8,
                created_by_user_id=1,
                is_rework_order=True,
                parent_work_order_id=100,
                rework_reason_code=None,  # Invalid - missing reason code
                rework_mode=ReworkMode.CONSUME_ADDITIONAL_MATERIALS
            )

    def test_rework_order_requires_rework_mode(self):
        """Test that rework order must have rework mode"""
        with pytest.raises(ValueError, match="Rework order must have a rework mode"):
            ReworkOrderDomain(
                id=6,
                organization_id=1,
                plant_id=101,
                work_order_number="RW2024-006",
                material_id=1,
                order_type="REWORK",
                order_status="PLANNED",
                planned_quantity=50.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=3),
                priority=8,
                created_by_user_id=1,
                is_rework_order=True,
                parent_work_order_id=100,
                rework_reason_code="DEFECT_001",
                rework_mode=None  # Invalid - missing rework mode
            )

    def test_non_rework_order_cannot_have_parent(self):
        """Test that non-rework orders cannot have parent_work_order_id"""
        with pytest.raises(ValueError, match="Only rework orders can have a parent work order"):
            ReworkOrderDomain(
                id=7,
                organization_id=1,
                plant_id=101,
                work_order_number="WO2024-007",
                material_id=1,
                order_type="PRODUCTION",
                order_status="PLANNED",
                planned_quantity=100.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=5),
                priority=5,
                created_by_user_id=1,
                is_rework_order=False,
                parent_work_order_id=100,  # Invalid - production order with parent
                rework_reason_code=None,
                rework_mode=None
            )

    def test_rework_order_type_must_be_rework(self):
        """Test that rework orders must have order_type REWORK"""
        with pytest.raises(ValueError, match="Rework order must have order_type REWORK"):
            ReworkOrderDomain(
                id=8,
                organization_id=1,
                plant_id=101,
                work_order_number="RW2024-008",
                material_id=1,
                order_type="PRODUCTION",  # Invalid - should be REWORK
                order_status="PLANNED",
                planned_quantity=50.0,
                actual_quantity=0.0,
                start_date_planned=datetime.now(),
                end_date_planned=datetime.now() + timedelta(days=3),
                priority=8,
                created_by_user_id=1,
                is_rework_order=True,
                parent_work_order_id=100,
                rework_reason_code="DEFECT_001",
                rework_mode=ReworkMode.CONSUME_ADDITIONAL_MATERIALS
            )

    def test_get_rework_cycle_number(self):
        """Test getting rework cycle number from parent chain"""
        rework_order = ReworkOrderDomain(
            id=9,
            organization_id=1,
            plant_id=101,
            work_order_number="RW2024-009",
            material_id=1,
            order_type="REWORK",
            order_status="PLANNED",
            planned_quantity=50.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=3),
            priority=8,
            created_by_user_id=1,
            is_rework_order=True,
            parent_work_order_id=100,
            rework_reason_code="DEFECT_001",
            rework_mode=ReworkMode.CONSUME_ADDITIONAL_MATERIALS
        )

        # Initial rework should be cycle 1
        assert rework_order.get_rework_cycle_number() == 1

    def test_validate_material_consumption_mode(self):
        """Test that CONSUME_ADDITIONAL_MATERIALS mode requires material tracking"""
        rework_order = ReworkOrderDomain(
            id=10,
            organization_id=1,
            plant_id=101,
            work_order_number="RW2024-010",
            material_id=1,
            order_type="REWORK",
            order_status="PLANNED",
            planned_quantity=50.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=3),
            priority=8,
            created_by_user_id=1,
            is_rework_order=True,
            parent_work_order_id=100,
            rework_reason_code="DEFECT_001",
            rework_mode=ReworkMode.CONSUME_ADDITIONAL_MATERIALS
        )

        assert rework_order.requires_material_consumption() is True

    def test_validate_wip_reprocessing_mode(self):
        """Test that REPROCESS_EXISTING_WIP mode does not require new materials"""
        rework_order = ReworkOrderDomain(
            id=11,
            organization_id=1,
            plant_id=101,
            work_order_number="RW2024-011",
            material_id=1,
            order_type="REWORK",
            order_status="PLANNED",
            planned_quantity=50.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=3),
            priority=8,
            created_by_user_id=1,
            is_rework_order=True,
            parent_work_order_id=100,
            rework_reason_code="DEFECT_001",
            rework_mode=ReworkMode.REPROCESS_EXISTING_WIP
        )

        assert rework_order.requires_material_consumption() is False

    def test_validate_hybrid_mode_requires_materials(self):
        """Test that HYBRID mode requires material tracking"""
        rework_order = ReworkOrderDomain(
            id=12,
            organization_id=1,
            plant_id=101,
            work_order_number="RW2024-012",
            material_id=1,
            order_type="REWORK",
            order_status="PLANNED",
            planned_quantity=50.0,
            actual_quantity=0.0,
            start_date_planned=datetime.now(),
            end_date_planned=datetime.now() + timedelta(days=3),
            priority=8,
            created_by_user_id=1,
            is_rework_order=True,
            parent_work_order_id=100,
            rework_reason_code="DEFECT_001",
            rework_mode=ReworkMode.HYBRID
        )

        assert rework_order.requires_material_consumption() is True
