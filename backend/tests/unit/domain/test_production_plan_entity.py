"""
Unit tests for ProductionPlan entity.
Phase 3: Production Planning Module - Component 3
"""
import pytest
from datetime import datetime, timedelta
from app.domain.entities.production_plan import ProductionPlan, PlanType, PlanStatus


class TestProductionPlanEntity:
    """Test suite for ProductionPlan domain entity"""

    def test_create_production_plan(self):
        """Test creating a production plan"""
        plan = ProductionPlan(
            organization_id=1,
            plant_id=1,
            plan_number="PLAN-2025-11",
            plan_name="November Production Plan",
            plan_type=PlanType.MONTHLY,
            plan_period_start=datetime(2025, 11, 1),
            plan_period_end=datetime(2025, 11, 30),
            status=PlanStatus.DRAFT,
            created_by_user_id=1
        )

        assert plan.organization_id == 1
        assert plan.plant_id == 1
        assert plan.plan_number == "PLAN-2025-11"
        assert plan.plan_name == "November Production Plan"
        assert plan.plan_type == PlanType.MONTHLY
        assert plan.status == PlanStatus.DRAFT

    def test_approve_production_plan(self):
        """Test approving a production plan"""
        plan = ProductionPlan(
            organization_id=1,
            plant_id=1,
            plan_number="PLAN-2025-11",
            plan_name="November Production Plan",
            plan_type=PlanType.MONTHLY,
            plan_period_start=datetime(2025, 11, 1),
            plan_period_end=datetime(2025, 11, 30),
            status=PlanStatus.DRAFT,
            created_by_user_id=1
        )

        plan.approve()

        assert plan.status == PlanStatus.APPROVED

    def test_execute_production_plan(self):
        """Test executing an approved production plan"""
        plan = ProductionPlan(
            organization_id=1,
            plant_id=1,
            plan_number="PLAN-2025-11",
            plan_name="November Production Plan",
            plan_type=PlanType.MONTHLY,
            plan_period_start=datetime(2025, 11, 1),
            plan_period_end=datetime(2025, 11, 30),
            status=PlanStatus.APPROVED,
            created_by_user_id=1
        )

        plan.execute()

        assert plan.status == PlanStatus.EXECUTED

    def test_cannot_execute_draft_plan(self):
        """Test that draft plan cannot be executed without approval"""
        plan = ProductionPlan(
            organization_id=1,
            plant_id=1,
            plan_number="PLAN-2025-11",
            plan_name="November Production Plan",
            plan_type=PlanType.MONTHLY,
            plan_period_start=datetime(2025, 11, 1),
            plan_period_end=datetime(2025, 11, 30),
            status=PlanStatus.DRAFT,
            created_by_user_id=1
        )

        with pytest.raises(ValueError, match="Can only execute approved plans"):
            plan.execute()

    def test_cannot_approve_executed_plan(self):
        """Test that executed plan cannot be re-approved"""
        plan = ProductionPlan(
            organization_id=1,
            plant_id=1,
            plan_number="PLAN-2025-11",
            plan_name="November Production Plan",
            plan_type=PlanType.MONTHLY,
            plan_period_start=datetime(2025, 11, 1),
            plan_period_end=datetime(2025, 11, 30),
            status=PlanStatus.EXECUTED,
            created_by_user_id=1
        )

        with pytest.raises(ValueError, match="Can only approve draft plans"):
            plan.approve()

    def test_plan_types(self):
        """Test different plan types"""
        weekly_plan = ProductionPlan(
            organization_id=1,
            plant_id=1,
            plan_number="PLAN-W45",
            plan_name="Week 45 Plan",
            plan_type=PlanType.WEEKLY,
            plan_period_start=datetime(2025, 11, 1),
            plan_period_end=datetime(2025, 11, 7),
            status=PlanStatus.DRAFT,
            created_by_user_id=1
        )

        quarterly_plan = ProductionPlan(
            organization_id=1,
            plant_id=1,
            plan_number="PLAN-Q4",
            plan_name="Q4 Plan",
            plan_type=PlanType.QUARTERLY,
            plan_period_start=datetime(2025, 10, 1),
            plan_period_end=datetime(2025, 12, 31),
            status=PlanStatus.DRAFT,
            created_by_user_id=1
        )

        assert weekly_plan.plan_type == PlanType.WEEKLY
        assert quarterly_plan.plan_type == PlanType.QUARTERLY

    def test_plan_period_validation(self):
        """Test validation of plan period dates"""
        with pytest.raises(ValueError, match="Plan period end must be after start"):
            ProductionPlan(
                organization_id=1,
                plant_id=1,
                plan_number="PLAN-INVALID",
                plan_name="Invalid Plan",
                plan_type=PlanType.MONTHLY,
                plan_period_start=datetime(2025, 11, 30),
                plan_period_end=datetime(2025, 11, 1),  # End before start
                status=PlanStatus.DRAFT,
                created_by_user_id=1
            )
