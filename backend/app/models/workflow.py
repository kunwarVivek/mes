"""
Workflow Engine models for dynamic state management and approvals.

Supports:
- Multi-step workflows with configurable states and transitions
- Approval processes with due dates and escalation
- Conditional transitions based on field values or business logic
- Audit trail for all workflow events
- Integration with any entity type (NCR, Work Orders, Projects, etc.)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, UniqueConstraint, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


# ========== Enums ==========

class StateType(str, enum.Enum):
    """Type of workflow state"""
    INITIAL = "INITIAL"  # Starting state
    INTERMEDIATE = "INTERMEDIATE"  # In-progress state
    FINAL = "FINAL"  # End state (success)
    CANCELLED = "CANCELLED"  # End state (cancelled)
    REJECTED = "REJECTED"  # End state (rejected)


class ApprovalStatus(str, enum.Enum):
    """Status of approval request"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"


class ApprovalPriority(str, enum.Enum):
    """Priority level for approval requests"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ========== Models ==========

class Workflow(Base):
    """
    Workflow definition with states and transitions.

    A workflow defines the lifecycle of an entity (NCR, Work Order, etc.)
    with states and allowed transitions between them.
    """
    __tablename__ = 'workflows'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Workflow identification
    workflow_name = Column(String(100), nullable=False)
    workflow_code = Column(String(50), nullable=False)  # Unique identifier per org
    description = Column(Text, nullable=True)

    # Entity binding
    entity_type = Column(String(50), nullable=False)  # material, work_order, ncr, project, etc.

    # System vs custom workflows
    is_system_workflow = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # JSONB configuration
    # {
    #   "allow_skip_states": false,
    #   "require_comment_on_transition": true,
    #   "auto_assign_on_transition": true,
    #   "notification_config": {
    #     "on_state_change": ["email", "in_app"],
    #     "on_approval_request": ["email"]
    #   }
    # }
    config = Column(JSONB, nullable=False, default={})

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    states = relationship("WorkflowState", back_populates="workflow", cascade="all, delete-orphan")
    transitions = relationship("WorkflowTransition", back_populates="workflow", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'workflow_code', name='uq_workflow_code_per_org'),
        UniqueConstraint('organization_id', 'entity_type', name='uq_workflow_per_entity_type'),
        Index('idx_workflow_org', 'organization_id'),
        Index('idx_workflow_entity', 'organization_id', 'entity_type'),
        Index('idx_workflow_active', 'organization_id', 'is_active'),
    )

    def __repr__(self):
        return f"<Workflow(id={self.id}, code='{self.workflow_code}', entity='{self.entity_type}')>"

    def get_initial_state(self):
        """Get the initial state of this workflow."""
        for state in self.states:
            if state.state_type == StateType.INITIAL:
                return state
        return None

    def get_final_states(self):
        """Get all final states (FINAL, CANCELLED, REJECTED)."""
        return [
            state for state in self.states
            if state.state_type in (StateType.FINAL, StateType.CANCELLED, StateType.REJECTED)
        ]


class WorkflowState(Base):
    """
    Individual state within a workflow.

    Each state represents a phase in the entity lifecycle.
    """
    __tablename__ = 'workflow_states'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)

    # State identification
    state_name = Column(String(100), nullable=False)
    state_code = Column(String(50), nullable=False)  # Unique within workflow
    description = Column(Text, nullable=True)

    # State type
    state_type = Column(SQLEnum(StateType), nullable=False, default=StateType.INTERMEDIATE)

    # Display configuration
    display_order = Column(Integer, nullable=False, default=0)
    color = Column(String(20), nullable=True)  # Hex color for UI
    icon = Column(String(50), nullable=True)  # Icon name

    # State behavior
    requires_approval = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # JSONB actions to execute when entering this state
    # {
    #   "assign_to_role": "QUALITY_MANAGER",
    #   "assign_to_user": 123,
    #   "send_notification": ["email", "in_app"],
    #   "update_fields": {"priority": "HIGH"},
    #   "trigger_webhook": "https://api.example.com/webhook"
    # }
    actions = Column(JSONB, nullable=True)

    # JSONB metadata
    # {
    #   "sla_hours": 24,
    #   "escalation_hours": 48,
    #   "editable_fields": ["description", "notes"],
    #   "readonly_fields": ["created_by", "created_at"]
    # }
    metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workflow = relationship("Workflow", back_populates="states")
    transitions_from = relationship(
        "WorkflowTransition",
        foreign_keys="WorkflowTransition.from_state_id",
        back_populates="from_state"
    )
    transitions_to = relationship(
        "WorkflowTransition",
        foreign_keys="WorkflowTransition.to_state_id",
        back_populates="to_state"
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint('workflow_id', 'state_code', name='uq_state_code_per_workflow'),
        Index('idx_workflow_states_org', 'organization_id'),
        Index('idx_workflow_states_workflow', 'workflow_id'),
        Index('idx_workflow_states_type', 'workflow_id', 'state_type'),
    )

    def __repr__(self):
        return f"<WorkflowState(id={self.id}, code='{self.state_code}', type='{self.state_type}')>"

    def get_available_transitions(self, context: dict = None):
        """
        Get available transitions from this state based on conditions.

        Args:
            context: Dictionary with entity data for condition evaluation

        Returns:
            List of available WorkflowTransition objects
        """
        available = []
        for transition in self.transitions_from:
            if not transition.is_active:
                continue

            # Check conditions if provided
            if transition.conditions and context:
                if not transition.evaluate_conditions(context):
                    continue

            available.append(transition)

        return available


class WorkflowTransition(Base):
    """
    Allowed transition between two workflow states.

    Defines rules, conditions, and actions for moving between states.
    """
    __tablename__ = 'workflow_transitions'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)

    # Transition definition
    from_state_id = Column(Integer, ForeignKey('workflow_states.id', ondelete='CASCADE'), nullable=False)
    to_state_id = Column(Integer, ForeignKey('workflow_states.id', ondelete='CASCADE'), nullable=False)

    # Transition identification
    transition_name = Column(String(100), nullable=False)
    transition_code = Column(String(50), nullable=False)  # Unique within workflow
    description = Column(Text, nullable=True)

    # Transition behavior
    requires_approval = Column(Boolean, nullable=False, default=False)
    requires_comment = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # JSONB conditions for allowing this transition
    # {
    #   "field_conditions": [
    #     {"field": "priority", "operator": "equals", "value": "HIGH"},
    #     {"field": "cost", "operator": "greater_than", "value": 1000}
    #   ],
    #   "role_conditions": ["QUALITY_MANAGER", "PRODUCTION_SUPERVISOR"],
    #   "custom_logic": "entity.defect_count > 5"
    # }
    conditions = Column(JSONB, nullable=True)

    # JSONB actions to execute when transition is taken
    # {
    #   "update_fields": {"status": "IN_REVIEW"},
    #   "create_approval": {"approver_role": "QUALITY_MANAGER", "due_hours": 24},
    #   "send_notification": ["email"],
    #   "assign_to": 123
    # }
    actions = Column(JSONB, nullable=True)

    # UI configuration
    display_order = Column(Integer, nullable=False, default=0)
    button_label = Column(String(100), nullable=True)  # Custom button text
    button_color = Column(String(20), nullable=True)  # Button color

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workflow = relationship("Workflow", back_populates="transitions")
    from_state = relationship("WorkflowState", foreign_keys=[from_state_id], back_populates="transitions_from")
    to_state = relationship("WorkflowState", foreign_keys=[to_state_id], back_populates="transitions_to")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('workflow_id', 'transition_code', name='uq_transition_code_per_workflow'),
        UniqueConstraint('from_state_id', 'to_state_id', name='uq_transition_between_states'),
        Index('idx_workflow_transitions_org', 'organization_id'),
        Index('idx_workflow_transitions_workflow', 'workflow_id'),
        Index('idx_workflow_transitions_from', 'from_state_id'),
        Index('idx_workflow_transitions_to', 'to_state_id'),
    )

    def __repr__(self):
        return f"<WorkflowTransition(id={self.id}, code='{self.transition_code}')>"

    def evaluate_conditions(self, context: dict) -> bool:
        """
        Evaluate if this transition's conditions are met.

        Args:
            context: Dictionary with entity data (fields, user roles, etc.)

        Returns:
            True if all conditions are met, False otherwise
        """
        if not self.conditions:
            return True

        # Evaluate field conditions
        field_conditions = self.conditions.get('field_conditions', [])
        for condition in field_conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            expected_value = condition.get('value')
            actual_value = context.get(field)

            if operator == 'equals' and actual_value != expected_value:
                return False
            elif operator == 'not_equals' and actual_value == expected_value:
                return False
            elif operator == 'greater_than' and not (actual_value and actual_value > expected_value):
                return False
            elif operator == 'less_than' and not (actual_value and actual_value < expected_value):
                return False
            elif operator == 'in' and actual_value not in expected_value:
                return False
            elif operator == 'not_in' and actual_value in expected_value:
                return False

        # Evaluate role conditions
        role_conditions = self.conditions.get('role_conditions', [])
        if role_conditions:
            user_roles = context.get('user_roles', [])
            if not any(role in user_roles for role in role_conditions):
                return False

        return True


class Approval(Base):
    """
    Approval request for workflow transitions or state changes.

    Tracks who needs to approve, deadline, and approval outcome.
    """
    __tablename__ = 'approvals'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Entity reference
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False, index=True)

    # Workflow reference (optional)
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='SET NULL'), nullable=True)
    workflow_state_id = Column(Integer, ForeignKey('workflow_states.id', ondelete='SET NULL'), nullable=True)

    # Approval details
    approval_type = Column(String(50), nullable=False)  # state_change, transition, manual
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Approver assignment
    approver_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approver_role = Column(String(50), nullable=True)  # If assigned to role instead of specific user

    # Status and outcome
    status = Column(SQLEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    priority = Column(SQLEnum(ApprovalPriority), nullable=False, default=ApprovalPriority.MEDIUM)

    # Comments
    request_comment = Column(Text, nullable=True)
    approval_comment = Column(Text, nullable=True)

    # Timing
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    requested_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # JSONB metadata
    # {
    #   "escalation_hours": 48,
    #   "escalate_to_user": 123,
    #   "escalate_to_role": "PLANT_MANAGER",
    #   "auto_approve_after_hours": 72,
    #   "related_approvals": [456, 789],
    #   "approval_criteria": {"cost_threshold": 5000}
    # }
    metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    history_entries = relationship("WorkflowHistory", back_populates="approval", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        Index('idx_approvals_org', 'organization_id'),
        Index('idx_approvals_entity', 'entity_type', 'entity_id'),
        Index('idx_approvals_approver', 'approver_user_id', 'status'),
        Index('idx_approvals_status', 'organization_id', 'status'),
        Index('idx_approvals_priority', 'organization_id', 'priority', 'status'),
    )

    def __repr__(self):
        return f"<Approval(id={self.id}, entity={self.entity_type}:{self.entity_id}, status='{self.status}')>"

    def is_overdue(self) -> bool:
        """Check if this approval is overdue."""
        if not self.due_date or self.status != ApprovalStatus.PENDING:
            return False

        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.due_date


class WorkflowHistory(Base):
    """
    Audit trail for all workflow events.

    Tracks state changes, transitions, approvals, and other workflow events.
    """
    __tablename__ = 'workflow_history'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Entity reference
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False, index=True)

    # Workflow reference
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='SET NULL'), nullable=True)

    # State tracking
    from_state_id = Column(Integer, ForeignKey('workflow_states.id', ondelete='SET NULL'), nullable=True)
    to_state_id = Column(Integer, ForeignKey('workflow_states.id', ondelete='SET NULL'), nullable=True)

    # Transition tracking (if applicable)
    transition_id = Column(Integer, ForeignKey('workflow_transitions.id', ondelete='SET NULL'), nullable=True)

    # Approval tracking (if applicable)
    approval_id = Column(Integer, ForeignKey('approvals.id', ondelete='SET NULL'), nullable=True)

    # Event details
    event_type = Column(String(50), nullable=False)  # state_change, approval_request, approval_response, comment, etc.
    event_description = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)

    # Actor
    performed_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    performed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # JSONB additional data
    # {
    #   "field_changes": {"priority": {"from": "LOW", "to": "HIGH"}},
    #   "system_action": true,
    #   "ip_address": "192.168.1.1",
    #   "user_agent": "Mozilla/5.0...",
    #   "duration_in_state": 3600
    # }
    metadata = Column(JSONB, nullable=True)

    # Relationships
    approval = relationship("Approval", back_populates="history_entries")

    # Table constraints
    __table_args__ = (
        Index('idx_workflow_history_org', 'organization_id'),
        Index('idx_workflow_history_entity', 'entity_type', 'entity_id'),
        Index('idx_workflow_history_workflow', 'workflow_id'),
        Index('idx_workflow_history_performed', 'performed_by', 'performed_at'),
        Index('idx_workflow_history_event', 'event_type', 'performed_at'),
    )

    def __repr__(self):
        return f"<WorkflowHistory(id={self.id}, entity={self.entity_type}:{self.entity_id}, event='{self.event_type}')>"
