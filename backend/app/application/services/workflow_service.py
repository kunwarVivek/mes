"""
Workflow Service - State machine engine for workflow management

Provides business logic for:
- State transitions with validation
- Approval workflows
- Condition evaluation
- Action execution
- Audit logging
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.models.workflow import (
    Workflow,
    WorkflowState,
    WorkflowTransition,
    Approval,
    WorkflowHistory,
    StateType,
    ApprovalStatus,
    ApprovalPriority,
)
from app.infrastructure.repositories.workflow_repository import (
    WorkflowRepository,
    WorkflowStateRepository,
    WorkflowTransitionRepository,
    ApprovalRepository,
    WorkflowHistoryRepository,
)


class WorkflowService:
    """Service for Workflow Engine operations - State machine and approval logic"""

    def __init__(self, db: Session):
        self.db = db
        self.workflow_repo = WorkflowRepository(db)
        self.state_repo = WorkflowStateRepository(db)
        self.transition_repo = WorkflowTransitionRepository(db)
        self.approval_repo = ApprovalRepository(db)
        self.history_repo = WorkflowHistoryRepository(db)

    # ========== Workflow Management ==========

    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Get workflow by ID"""
        return self.workflow_repo.get_by_id(workflow_id)

    def get_workflow_for_entity(self, organization_id: int, entity_type: str) -> Optional[Workflow]:
        """Get the default workflow for an entity type"""
        return self.workflow_repo.get_default_workflow(organization_id, entity_type)

    def get_workflow_with_details(self, workflow_id: int) -> Optional[Workflow]:
        """Get workflow with states and transitions loaded"""
        return self.workflow_repo.get_workflow_with_transitions(workflow_id)

    # ========== State Transition Engine ==========

    def execute_transition(
        self,
        entity_type: str,
        entity_id: int,
        transition_id: int,
        actor_id: int,
        entity_data: Optional[Dict[str, Any]] = None,
        user_roles: Optional[List[str]] = None,
        comments: Optional[str] = None,
        organization_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Optional[WorkflowState]]:
        """
        Execute a workflow transition with full validation.

        Args:
            entity_type: Type of entity (ncr, work_order, etc.)
            entity_id: Entity ID
            transition_id: Transition to execute
            actor_id: User performing the transition
            entity_data: Current entity data for condition evaluation
            user_roles: Actor's roles for permission checking
            comments: Optional comments for the transition
            organization_id: Organization ID

        Returns:
            (success, error_message, new_state)
        """
        # Get the transition
        transition = self.transition_repo.get_by_id(transition_id)
        if not transition:
            return False, f"Transition {transition_id} not found", None

        if not transition.is_active:
            return False, f"Transition '{transition.transition_name}' is not active", None

        # Validate transition is allowed
        is_valid, error_msg = self.validate_transition(
            transition, entity_data or {}, user_roles or []
        )
        if not is_valid:
            return False, error_msg, None

        # Check if comments are required
        if transition.requires_comment and not comments:
            return False, "Comments are required for this transition", None

        # Get workflow and states
        workflow = self.workflow_repo.get_by_id(transition.workflow_id)
        from_state = self.state_repo.get_by_id(transition.from_state_id)
        to_state = self.state_repo.get_by_id(transition.to_state_id)

        if not organization_id:
            organization_id = workflow.organization_id

        try:
            # Execute pre-transition actions
            if transition.actions and 'pre_actions' in transition.actions:
                self._execute_actions(
                    transition.actions['pre_actions'],
                    entity_type,
                    entity_id,
                    workflow,
                    to_state,
                    actor_id
                )

            # Create approval if required
            if transition.requires_approval:
                approval = self.request_approval(
                    organization_id=organization_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    workflow_id=workflow.id,
                    workflow_state_id=to_state.id,
                    requested_by=actor_id,
                    transition=transition,
                    comments=comments
                )

                # Record transition attempt (pending approval)
                self.history_repo.record_history(
                    organization_id=organization_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    workflow_id=workflow.id,
                    from_state_id=from_state.id,
                    to_state_id=to_state.id,
                    transition_id=transition.id,
                    event_type='transition_pending_approval',
                    event_description=f"Transition '{transition.transition_name}' initiated, pending approval",
                    performed_by=actor_id,
                    comment=comments,
                    metadata={'approval_id': approval.id}
                )

                return True, f"Transition initiated. Approval required from {approval.approver_role or 'assigned user'}.", to_state

            # Execute post-transition actions
            if transition.actions and 'post_actions' in transition.actions:
                self._execute_actions(
                    transition.actions['post_actions'],
                    entity_type,
                    entity_id,
                    workflow,
                    to_state,
                    actor_id
                )

            # Execute state entry actions
            if to_state.actions:
                self._execute_actions(
                    [to_state.actions] if isinstance(to_state.actions, dict) else to_state.actions,
                    entity_type,
                    entity_id,
                    workflow,
                    to_state,
                    actor_id
                )

            # Record successful transition
            self.history_repo.record_history(
                organization_id=organization_id,
                entity_type=entity_type,
                entity_id=entity_id,
                workflow_id=workflow.id,
                from_state_id=from_state.id,
                to_state_id=to_state.id,
                transition_id=transition.id,
                event_type='transition',
                event_description=f"Transitioned from '{from_state.state_name}' to '{to_state.state_name}'",
                performed_by=actor_id,
                comment=comments
            )

            self.db.commit()
            return True, None, to_state

        except Exception as e:
            self.db.rollback()
            return False, f"Transition failed: {str(e)}", None

    def validate_transition(
        self,
        transition: WorkflowTransition,
        entity_data: Dict[str, Any],
        user_roles: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if a transition is allowed based on conditions.

        Args:
            transition: The transition to validate
            entity_data: Current entity data
            user_roles: User's roles

        Returns:
            (is_valid, error_message)
        """
        if not transition.conditions:
            return True, None

        conditions = transition.conditions

        # Check required roles
        required_roles = conditions.get('required_roles', [])
        if required_roles:
            if not any(role in user_roles for role in required_roles):
                return False, f"User must have one of these roles: {', '.join(required_roles)}"

        # Check required fields
        required_fields = conditions.get('required_fields', [])
        for field in required_fields:
            if field not in entity_data or entity_data[field] is None or entity_data[field] == '':
                return False, f"Required field '{field}' is missing or empty"

        # Check custom conditions
        custom_conditions = conditions.get('custom_conditions', [])
        for condition in custom_conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            expected_value = condition.get('value')
            actual_value = entity_data.get(field)

            if operator == 'equals' and actual_value != expected_value:
                return False, f"Field '{field}' must equal '{expected_value}'"
            elif operator == 'not_equals' and actual_value == expected_value:
                return False, f"Field '{field}' must not equal '{expected_value}'"
            elif operator == 'in' and actual_value not in expected_value:
                return False, f"Field '{field}' must be one of: {expected_value}"
            elif operator == 'not_in' and actual_value in expected_value:
                return False, f"Field '{field}' must not be one of: {expected_value}"
            elif operator == 'greater_than':
                if actual_value is None or actual_value <= expected_value:
                    return False, f"Field '{field}' must be greater than {expected_value}"
            elif operator == 'less_than':
                if actual_value is None or actual_value >= expected_value:
                    return False, f"Field '{field}' must be less than {expected_value}"
            elif operator == 'contains' and expected_value not in str(actual_value):
                return False, f"Field '{field}' must contain '{expected_value}'"

        return True, None

    def get_available_transitions(
        self,
        from_state_id: int,
        entity_data: Optional[Dict[str, Any]] = None,
        user_roles: Optional[List[str]] = None
    ) -> List[WorkflowTransition]:
        """
        Get available transitions from a state, filtered by conditions.

        Args:
            from_state_id: Current state ID
            entity_data: Entity data for condition evaluation
            user_roles: User's roles for permission checking

        Returns:
            List of available transitions
        """
        all_transitions = self.transition_repo.get_available_transitions(from_state_id)

        if not entity_data and not user_roles:
            return all_transitions

        available = []
        for transition in all_transitions:
            is_valid, _ = self.validate_transition(
                transition,
                entity_data or {},
                user_roles or []
            )
            if is_valid:
                available.append(transition)

        return available

    # ========== Approval Management ==========

    def request_approval(
        self,
        organization_id: int,
        entity_type: str,
        entity_id: int,
        workflow_id: int,
        workflow_state_id: int,
        requested_by: int,
        transition: Optional[WorkflowTransition] = None,
        approver_user_id: Optional[int] = None,
        approver_role: Optional[str] = None,
        comments: Optional[str] = None,
        due_hours: int = 48,
        priority: ApprovalPriority = ApprovalPriority.MEDIUM
    ) -> Approval:
        """
        Create an approval request.

        Args:
            organization_id: Organization ID
            entity_type: Type of entity
            entity_id: Entity ID
            workflow_id: Workflow ID
            workflow_state_id: Target state ID
            requested_by: User requesting approval
            transition: Optional transition being executed
            approver_user_id: Specific user to approve (optional)
            approver_role: Role that can approve (optional)
            comments: Request comments
            due_hours: Hours until due (default 48)
            priority: Priority level

        Returns:
            Created Approval
        """
        # Determine approver from transition actions if not specified
        if not approver_user_id and not approver_role and transition:
            if transition.actions and 'create_approval' in transition.actions:
                approval_config = transition.actions['create_approval']
                approver_role = approval_config.get('approver_role')
                approver_user_id = approval_config.get('approver_user_id')
                due_hours = approval_config.get('due_hours', due_hours)

        # Calculate due date
        due_date = datetime.now(timezone.utc) + timedelta(hours=due_hours)

        # Create title
        state = self.state_repo.get_by_id(workflow_state_id)
        title = f"Approval required for {entity_type} #{entity_id}"
        if state:
            title += f" - {state.state_name}"

        approval = self.approval_repo.create(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            workflow_id=workflow_id,
            workflow_state_id=workflow_state_id,
            approval_type='transition',
            title=title,
            approver_user_id=approver_user_id,
            approver_role=approver_role,
            description=f"Approval required for workflow transition",
            request_comment=comments,
            requested_by=requested_by,
            due_date=due_date,
            priority=priority
        )

        # Record history
        self.history_repo.record_history(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            workflow_id=workflow_id,
            to_state_id=workflow_state_id,
            approval_id=approval.id,
            event_type='approval_requested',
            event_description=f"Approval requested from {approver_role or 'user'}",
            performed_by=requested_by,
            comment=comments
        )

        return approval

    def process_approval(
        self,
        approval_id: int,
        approver_id: int,
        approved: bool,
        comments: Optional[str] = None,
        entity_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], Optional[WorkflowState]]:
        """
        Process an approval (approve or reject).

        Args:
            approval_id: Approval ID
            approver_id: User approving/rejecting
            approved: True to approve, False to reject
            comments: Approval comments
            entity_data: Entity data for executing transition

        Returns:
            (success, error_message, new_state)
        """
        approval = self.approval_repo.get_by_id(approval_id)
        if not approval:
            return False, f"Approval {approval_id} not found", None

        if approval.status != ApprovalStatus.PENDING:
            return False, f"Approval is already {approval.status.value}", None

        # Verify approver has permission
        if approval.approver_user_id and approval.approver_user_id != approver_id:
            return False, "You are not authorized to process this approval", None

        try:
            if approved:
                # Approve the approval
                self.approval_repo.approve(approval_id, approver_id, comments)

                # Find the transition that triggered this approval
                # and complete the state change
                if approval.workflow_state_id:
                    to_state = self.state_repo.get_by_id(approval.workflow_state_id)

                    # Execute state entry actions
                    if to_state and to_state.actions:
                        self._execute_actions(
                            [to_state.actions] if isinstance(to_state.actions, dict) else to_state.actions,
                            approval.entity_type,
                            approval.entity_id,
                            None,
                            to_state,
                            approver_id
                        )

                    # Record approval in history
                    self.history_repo.record_history(
                        organization_id=approval.organization_id,
                        entity_type=approval.entity_type,
                        entity_id=approval.entity_id,
                        workflow_id=approval.workflow_id,
                        to_state_id=approval.workflow_state_id,
                        approval_id=approval.id,
                        event_type='approval_granted',
                        event_description=f"Approval granted by user {approver_id}",
                        performed_by=approver_id,
                        comment=comments
                    )

                    self.db.commit()
                    return True, "Approval granted", to_state

            else:
                # Reject the approval
                self.approval_repo.reject(approval_id, approver_id, comments)

                # Record rejection in history
                self.history_repo.record_history(
                    organization_id=approval.organization_id,
                    entity_type=approval.entity_type,
                    entity_id=approval.entity_id,
                    workflow_id=approval.workflow_id,
                    approval_id=approval.id,
                    event_type='approval_rejected',
                    event_description=f"Approval rejected by user {approver_id}",
                    performed_by=approver_id,
                    comment=comments
                )

                self.db.commit()
                return True, "Approval rejected", None

        except Exception as e:
            self.db.rollback()
            return False, f"Failed to process approval: {str(e)}", None

    def get_pending_approvals(self, user_id: int, organization_id: Optional[int] = None) -> List[Approval]:
        """Get all pending approvals for a user"""
        return self.approval_repo.get_pending_approvals(user_id, organization_id)

    def get_pending_approvals_by_role(self, role: str, organization_id: int) -> List[Approval]:
        """Get all pending approvals for a role"""
        return self.approval_repo.get_pending_approvals_by_role(role, organization_id)

    # ========== Entity Workflow Status ==========

    def get_entity_workflow_status(
        self,
        entity_type: str,
        entity_id: int,
        current_state_id: int,
        entity_data: Optional[Dict[str, Any]] = None,
        user_roles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get complete workflow status for an entity.

        Returns current state, available transitions, and pending approvals.

        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            current_state_id: Current state ID
            entity_data: Entity data for condition evaluation
            user_roles: User's roles

        Returns:
            Dictionary with workflow status information
        """
        current_state = self.state_repo.get_by_id(current_state_id)
        if not current_state:
            return {
                'error': 'Current state not found',
                'current_state': None,
                'available_transitions': [],
                'pending_approvals': []
            }

        # Get available transitions
        available_transitions = self.get_available_transitions(
            current_state_id,
            entity_data,
            user_roles
        )

        # Get pending approvals
        pending_approvals = self.approval_repo.get_entity_approvals(
            entity_type,
            entity_id,
            ApprovalStatus.PENDING
        )

        return {
            'current_state': {
                'id': current_state.id,
                'code': current_state.state_code,
                'name': current_state.state_name,
                'type': current_state.state_type.value,
                'color': current_state.color,
                'icon': current_state.icon,
                'requires_approval': current_state.requires_approval,
            },
            'available_transitions': [
                {
                    'id': t.id,
                    'code': t.transition_code,
                    'name': t.transition_name,
                    'to_state': {
                        'id': t.to_state.id,
                        'code': t.to_state.state_code,
                        'name': t.to_state.state_name,
                    },
                    'requires_approval': t.requires_approval,
                    'requires_comment': t.requires_comment,
                }
                for t in available_transitions
            ],
            'pending_approvals': [
                {
                    'id': a.id,
                    'title': a.title,
                    'status': a.status.value,
                    'priority': a.priority.value,
                    'requested_at': a.requested_at.isoformat(),
                    'due_date': a.due_date.isoformat() if a.due_date else None,
                }
                for a in pending_approvals
            ]
        }

    # ========== Action Execution ==========

    def auto_execute_actions(
        self,
        actions: List[Dict[str, Any]],
        entity_type: str,
        entity_id: int,
        workflow: Optional[Workflow],
        state: WorkflowState,
        actor_id: int
    ) -> None:
        """
        Execute post-transition or state-entry actions.

        This is a public wrapper for _execute_actions.
        """
        self._execute_actions(actions, entity_type, entity_id, workflow, state, actor_id)

    def _execute_actions(
        self,
        actions: List[Dict[str, Any]],
        entity_type: str,
        entity_id: int,
        workflow: Optional[Workflow],
        state: WorkflowState,
        actor_id: int
    ) -> None:
        """
        Execute a list of actions.

        Supported actions:
        - send_notification: Send notification to users/roles
        - update_entity: Update entity fields
        - create_approval: Create approval request
        - assign_to: Assign entity to user

        Args:
            actions: List of action definitions
            entity_type: Type of entity
            entity_id: Entity ID
            workflow: Workflow (optional)
            state: Target state
            actor_id: User performing the action
        """
        for action in actions:
            action_type = action.get('action')
            params = action.get('params', {})

            if action_type == 'send_notification':
                self._send_notification(
                    entity_type, entity_id, params, actor_id
                )
            elif action_type == 'update_entity':
                # This would need to be implemented based on entity type
                # For now, just log it
                pass
            elif action_type == 'create_approval':
                # This is handled separately in execute_transition
                pass
            elif action_type == 'assign_to':
                # This would need entity-specific implementation
                pass

    def _send_notification(
        self,
        entity_type: str,
        entity_id: int,
        params: Dict[str, Any],
        actor_id: int
    ) -> None:
        """
        Send notification (placeholder for actual implementation).

        This would integrate with an email/notification service.
        """
        # TODO: Implement notification sending
        # This would call an EmailService or NotificationService
        pass

    # ========== History and Audit ==========

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowHistory]:
        """Get workflow history for an entity"""
        return self.history_repo.get_entity_history(entity_type, entity_id, skip, limit)

    def record_comment(
        self,
        organization_id: int,
        entity_type: str,
        entity_id: int,
        workflow_id: int,
        current_state_id: int,
        actor_id: int,
        comment: str
    ) -> WorkflowHistory:
        """Record a comment in workflow history"""
        return self.history_repo.record_history(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            workflow_id=workflow_id,
            to_state_id=current_state_id,
            event_type='comment',
            event_description='Comment added',
            performed_by=actor_id,
            comment=comment
        )
