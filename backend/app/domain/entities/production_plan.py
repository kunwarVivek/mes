"""
Domain entity for Production Plan.
Phase 3: Production Planning Module - Component 3
"""
import enum
from datetime import datetime


class PlanType(str, enum.Enum):
    """Enum for production plan types"""
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"


class PlanStatus(str, enum.Enum):
    """Enum for production plan status"""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"


class ProductionPlan:
    """
    Production Plan domain entity - groups work orders into planning horizons.

    Represents a production plan for a specific time period (weekly/monthly/quarterly).
    Manages status transitions from draft to approved to executed.
    """

    def __init__(
        self,
        organization_id: int,
        plant_id: int,
        plan_number: str,
        plan_name: str,
        plan_type: PlanType,
        plan_period_start: datetime,
        plan_period_end: datetime,
        status: PlanStatus,
        created_by_user_id: int,
        id: int = None,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        """
        Initialize ProductionPlan entity.

        Args:
            organization_id: Organization ID for multi-tenancy
            plant_id: Plant ID for multi-tenancy
            plan_number: Unique plan identifier
            plan_name: Descriptive plan name
            plan_type: Type of plan (WEEKLY/MONTHLY/QUARTERLY)
            plan_period_start: Plan period start date
            plan_period_end: Plan period end date
            status: Plan status
            created_by_user_id: User who created the plan
            id: Entity ID (optional, for persistence)
            created_at: Creation timestamp (optional)
            updated_at: Last update timestamp (optional)

        Raises:
            ValueError: If plan period end is not after start
        """
        if plan_period_end <= plan_period_start:
            raise ValueError("Plan period end must be after start")

        self.id = id
        self.organization_id = organization_id
        self.plant_id = plant_id
        self.plan_number = plan_number
        self.plan_name = plan_name
        self.plan_type = plan_type
        self.plan_period_start = plan_period_start
        self.plan_period_end = plan_period_end
        self.status = status
        self.created_by_user_id = created_by_user_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at

    def approve(self) -> None:
        """
        Approve the production plan.

        Transitions status from DRAFT to APPROVED.

        Raises:
            ValueError: If plan is not in DRAFT status
        """
        if self.status != PlanStatus.DRAFT:
            raise ValueError("Can only approve draft plans")

        self.status = PlanStatus.APPROVED
        self.updated_at = datetime.now()

    def execute(self) -> None:
        """
        Execute the production plan.

        Transitions status from APPROVED to EXECUTED.
        Generates work orders for planned production.

        Raises:
            ValueError: If plan is not in APPROVED status
        """
        if self.status != PlanStatus.APPROVED:
            raise ValueError("Can only execute approved plans")

        self.status = PlanStatus.EXECUTED
        self.updated_at = datetime.now()

    def generate_work_orders(self):
        """
        Generate work orders from production plan.

        This method would create work orders based on the plan's requirements.
        Implementation depends on specific business requirements.
        """
        # Placeholder for work order generation logic
        # In real implementation, this would:
        # 1. Analyze demand forecasts
        # 2. Check inventory levels
        # 3. Create work orders for required quantities
        # 4. Schedule operations based on capacity
        pass

    def __repr__(self):
        return f"<ProductionPlan(number='{self.plan_number}', type='{self.plan_type}', status='{self.status}')>"
