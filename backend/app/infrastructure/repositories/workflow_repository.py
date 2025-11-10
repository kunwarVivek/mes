"""
Repository for Workflow Engine operations

Provides data access layer for workflows, states, transitions, approvals, and history.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from datetime import datetime, timezone

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


class WorkflowRepository:
    """Repository for Workflow CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, organization_id: int, workflow_name: str, workflow_code: str,
               entity_type: str, description: Optional[str] = None,
               config: Optional[Dict[str, Any]] = None,
               created_by: Optional[int] = None) -> Workflow:
        """Create a new workflow"""
        workflow = Workflow(
            organization_id=organization_id,
            workflow_name=workflow_name,
            workflow_code=workflow_code,
            entity_type=entity_type,
            description=description,
            is_system_workflow=False,
            is_active=True,
            config=config or {},
            created_by=created_by,
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_by_id(self, workflow_id: int) -> Optional[Workflow]:
        """Get workflow by ID"""
        return self.db.query(Workflow).filter(Workflow.id == workflow_id).first()

    def get_by_code(self, organization_id: int, workflow_code: str) -> Optional[Workflow]:
        """Get workflow by code within an organization"""
        return self.db.query(Workflow).filter(
            and_(
                Workflow.organization_id == organization_id,
                Workflow.workflow_code == workflow_code
            )
        ).first()

    def get_default_workflow(self, organization_id: int, entity_type: str) -> Optional[Workflow]:
        """
        Get the default workflow for an entity type.
        For now, returns the first active workflow for the entity type.
        """
        return self.db.query(Workflow).filter(
            and_(
                Workflow.organization_id == organization_id,
                Workflow.entity_type == entity_type,
                Workflow.is_active == True
            )
        ).first()

    def get_workflow_with_states(self, workflow_id: int) -> Optional[Workflow]:
        """Get workflow with all states eagerly loaded"""
        return self.db.query(Workflow).options(
            joinedload(Workflow.states)
        ).filter(Workflow.id == workflow_id).first()

    def get_workflow_with_transitions(self, workflow_id: int) -> Optional[Workflow]:
        """Get workflow with states and transitions eagerly loaded"""
        return self.db.query(Workflow).options(
            joinedload(Workflow.states).joinedload(WorkflowState.transitions_from),
            joinedload(Workflow.transitions)
        ).filter(Workflow.id == workflow_id).first()

    def list_workflows(self, organization_id: int, entity_type: Optional[str] = None,
                      include_inactive: bool = False,
                      skip: int = 0, limit: int = 100) -> List[Workflow]:
        """List workflows with optional filters"""
        query = self.db.query(Workflow).filter(
            Workflow.organization_id == organization_id
        )

        if entity_type:
            query = query.filter(Workflow.entity_type == entity_type)

        if not include_inactive:
            query = query.filter(Workflow.is_active == True)

        return query.offset(skip).limit(limit).all()

    def update(self, workflow_id: int, updates: Dict[str, Any]) -> Optional[Workflow]:
        """Update workflow (cannot update system workflows)"""
        workflow = self.get_by_id(workflow_id)
        if not workflow:
            return None

        # Prevent updates to system workflows
        if workflow.is_system_workflow:
            raise ValueError("Cannot modify system workflows")

        for key, value in updates.items():
            if hasattr(workflow, key) and key not in ['id', 'organization_id', 'created_at', 'created_by']:
                setattr(workflow, key, value)

        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def delete(self, workflow_id: int) -> bool:
        """Delete workflow (cannot delete system workflows)"""
        workflow = self.get_by_id(workflow_id)
        if not workflow:
            return False

        # Prevent deletion of system workflows
        if workflow.is_system_workflow:
            raise ValueError("Cannot delete system workflows")

        self.db.delete(workflow)
        self.db.commit()
        return True


class WorkflowStateRepository:
    """Repository for WorkflowState CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, organization_id: int, workflow_id: int, state_name: str,
               state_code: str, state_type: StateType,
               description: Optional[str] = None,
               display_order: int = 0,
               color: Optional[str] = None,
               icon: Optional[str] = None,
               requires_approval: bool = False,
               actions: Optional[Dict[str, Any]] = None,
               metadata: Optional[Dict[str, Any]] = None) -> WorkflowState:
        """Create a new workflow state"""
        state = WorkflowState(
            organization_id=organization_id,
            workflow_id=workflow_id,
            state_name=state_name,
            state_code=state_code,
            state_type=state_type,
            description=description,
            display_order=display_order,
            color=color,
            icon=icon,
            requires_approval=requires_approval,
            is_active=True,
            actions=actions,
            metadata=metadata,
        )
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state

    def get_by_id(self, state_id: int) -> Optional[WorkflowState]:
        """Get state by ID"""
        return self.db.query(WorkflowState).filter(WorkflowState.id == state_id).first()

    def get_by_code(self, workflow_id: int, state_code: str) -> Optional[WorkflowState]:
        """Get state by code within a workflow"""
        return self.db.query(WorkflowState).filter(
            and_(
                WorkflowState.workflow_id == workflow_id,
                WorkflowState.state_code == state_code
            )
        ).first()

    def list_by_workflow(self, workflow_id: int, include_inactive: bool = False) -> List[WorkflowState]:
        """List all states for a workflow"""
        query = self.db.query(WorkflowState).filter(
            WorkflowState.workflow_id == workflow_id
        )

        if not include_inactive:
            query = query.filter(WorkflowState.is_active == True)

        return query.order_by(WorkflowState.display_order).all()

    def get_initial_state(self, workflow_id: int) -> Optional[WorkflowState]:
        """Get the initial state for a workflow"""
        return self.db.query(WorkflowState).filter(
            and_(
                WorkflowState.workflow_id == workflow_id,
                WorkflowState.state_type == StateType.INITIAL,
                WorkflowState.is_active == True
            )
        ).first()

    def update(self, state_id: int, updates: Dict[str, Any]) -> Optional[WorkflowState]:
        """Update workflow state"""
        state = self.get_by_id(state_id)
        if not state:
            return None

        for key, value in updates.items():
            if hasattr(state, key) and key not in ['id', 'organization_id', 'workflow_id', 'created_at']:
                setattr(state, key, value)

        self.db.commit()
        self.db.refresh(state)
        return state

    def delete(self, state_id: int) -> bool:
        """Delete workflow state"""
        state = self.get_by_id(state_id)
        if not state:
            return False

        self.db.delete(state)
        self.db.commit()
        return True


class WorkflowTransitionRepository:
    """Repository for WorkflowTransition CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, organization_id: int, workflow_id: int,
               from_state_id: int, to_state_id: int,
               transition_name: str, transition_code: str,
               description: Optional[str] = None,
               requires_approval: bool = False,
               requires_comment: bool = False,
               conditions: Optional[Dict[str, Any]] = None,
               actions: Optional[Dict[str, Any]] = None,
               display_order: int = 0) -> WorkflowTransition:
        """Create a new workflow transition"""
        transition = WorkflowTransition(
            organization_id=organization_id,
            workflow_id=workflow_id,
            from_state_id=from_state_id,
            to_state_id=to_state_id,
            transition_name=transition_name,
            transition_code=transition_code,
            description=description,
            requires_approval=requires_approval,
            requires_comment=requires_comment,
            is_active=True,
            conditions=conditions,
            actions=actions,
            display_order=display_order,
        )
        self.db.add(transition)
        self.db.commit()
        self.db.refresh(transition)
        return transition

    def get_by_id(self, transition_id: int) -> Optional[WorkflowTransition]:
        """Get transition by ID"""
        return self.db.query(WorkflowTransition).filter(
            WorkflowTransition.id == transition_id
        ).first()

    def get_by_code(self, workflow_id: int, transition_code: str) -> Optional[WorkflowTransition]:
        """Get transition by code within a workflow"""
        return self.db.query(WorkflowTransition).filter(
            and_(
                WorkflowTransition.workflow_id == workflow_id,
                WorkflowTransition.transition_code == transition_code
            )
        ).first()

    def get_available_transitions(self, from_state_id: int, include_inactive: bool = False) -> List[WorkflowTransition]:
        """Get all transitions available from a given state"""
        query = self.db.query(WorkflowTransition).options(
            joinedload(WorkflowTransition.to_state)
        ).filter(WorkflowTransition.from_state_id == from_state_id)

        if not include_inactive:
            query = query.filter(WorkflowTransition.is_active == True)

        return query.order_by(WorkflowTransition.display_order).all()

    def list_by_workflow(self, workflow_id: int, include_inactive: bool = False) -> List[WorkflowTransition]:
        """List all transitions for a workflow"""
        query = self.db.query(WorkflowTransition).filter(
            WorkflowTransition.workflow_id == workflow_id
        )

        if not include_inactive:
            query = query.filter(WorkflowTransition.is_active == True)

        return query.all()

    def update(self, transition_id: int, updates: Dict[str, Any]) -> Optional[WorkflowTransition]:
        """Update workflow transition"""
        transition = self.get_by_id(transition_id)
        if not transition:
            return None

        for key, value in updates.items():
            if hasattr(transition, key) and key not in ['id', 'organization_id', 'workflow_id', 'created_at']:
                setattr(transition, key, value)

        self.db.commit()
        self.db.refresh(transition)
        return transition

    def delete(self, transition_id: int) -> bool:
        """Delete workflow transition"""
        transition = self.get_by_id(transition_id)
        if not transition:
            return False

        self.db.delete(transition)
        self.db.commit()
        return True


class ApprovalRepository:
    """Repository for Approval CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, organization_id: int, entity_type: str, entity_id: int,
               approval_type: str, title: str,
               workflow_id: Optional[int] = None,
               workflow_state_id: Optional[int] = None,
               approver_user_id: Optional[int] = None,
               approver_role: Optional[str] = None,
               description: Optional[str] = None,
               request_comment: Optional[str] = None,
               requested_by: Optional[int] = None,
               due_date: Optional[datetime] = None,
               priority: ApprovalPriority = ApprovalPriority.MEDIUM,
               metadata: Optional[Dict[str, Any]] = None) -> Approval:
        """Create a new approval request"""
        approval = Approval(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            workflow_id=workflow_id,
            workflow_state_id=workflow_state_id,
            approval_type=approval_type,
            title=title,
            description=description,
            approver_user_id=approver_user_id,
            approver_role=approver_role,
            status=ApprovalStatus.PENDING,
            priority=priority,
            request_comment=request_comment,
            requested_by=requested_by,
            due_date=due_date,
            metadata=metadata,
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def get_by_id(self, approval_id: int) -> Optional[Approval]:
        """Get approval by ID"""
        return self.db.query(Approval).filter(Approval.id == approval_id).first()

    def get_pending_approvals(self, user_id: int, organization_id: Optional[int] = None) -> List[Approval]:
        """Get all pending approvals for a user"""
        query = self.db.query(Approval).filter(
            and_(
                Approval.approver_user_id == user_id,
                Approval.status == ApprovalStatus.PENDING
            )
        )

        if organization_id:
            query = query.filter(Approval.organization_id == organization_id)

        return query.order_by(
            Approval.priority.desc(),
            Approval.due_date.asc()
        ).all()

    def get_pending_approvals_by_role(self, role: str, organization_id: int) -> List[Approval]:
        """Get all pending approvals for a role"""
        return self.db.query(Approval).filter(
            and_(
                Approval.organization_id == organization_id,
                Approval.approver_role == role,
                Approval.status == ApprovalStatus.PENDING
            )
        ).order_by(
            Approval.priority.desc(),
            Approval.due_date.asc()
        ).all()

    def get_entity_approvals(self, entity_type: str, entity_id: int,
                            status: Optional[ApprovalStatus] = None) -> List[Approval]:
        """Get all approvals for an entity"""
        query = self.db.query(Approval).filter(
            and_(
                Approval.entity_type == entity_type,
                Approval.entity_id == entity_id
            )
        )

        if status:
            query = query.filter(Approval.status == status)

        return query.order_by(Approval.requested_at.desc()).all()

    def get_overdue_approvals(self, organization_id: int) -> List[Approval]:
        """Get all overdue pending approvals"""
        now = datetime.now(timezone.utc)
        return self.db.query(Approval).filter(
            and_(
                Approval.organization_id == organization_id,
                Approval.status == ApprovalStatus.PENDING,
                Approval.due_date.isnot(None),
                Approval.due_date < now
            )
        ).all()

    def update(self, approval_id: int, updates: Dict[str, Any]) -> Optional[Approval]:
        """Update approval"""
        approval = self.get_by_id(approval_id)
        if not approval:
            return None

        for key, value in updates.items():
            if hasattr(approval, key) and key not in ['id', 'organization_id', 'created_at', 'requested_at']:
                setattr(approval, key, value)

        self.db.commit()
        self.db.refresh(approval)
        return approval

    def approve(self, approval_id: int, approver_id: int, comment: Optional[str] = None) -> Optional[Approval]:
        """Approve an approval request"""
        approval = self.get_by_id(approval_id)
        if not approval:
            return None

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot approve: approval is already {approval.status.value}")

        approval.status = ApprovalStatus.APPROVED
        approval.approval_comment = comment
        approval.responded_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(approval)
        return approval

    def reject(self, approval_id: int, approver_id: int, comment: Optional[str] = None) -> Optional[Approval]:
        """Reject an approval request"""
        approval = self.get_by_id(approval_id)
        if not approval:
            return None

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot reject: approval is already {approval.status.value}")

        approval.status = ApprovalStatus.REJECTED
        approval.approval_comment = comment
        approval.responded_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(approval)
        return approval

    def cancel(self, approval_id: int) -> Optional[Approval]:
        """Cancel an approval request"""
        approval = self.get_by_id(approval_id)
        if not approval:
            return None

        approval.status = ApprovalStatus.CANCELLED
        approval.responded_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(approval)
        return approval


class WorkflowHistoryRepository:
    """Repository for WorkflowHistory (read-only audit log)"""

    def __init__(self, db: Session):
        self.db = db

    def record_history(self, organization_id: int, entity_type: str, entity_id: int,
                      event_type: str, event_description: Optional[str] = None,
                      workflow_id: Optional[int] = None,
                      from_state_id: Optional[int] = None,
                      to_state_id: Optional[int] = None,
                      transition_id: Optional[int] = None,
                      approval_id: Optional[int] = None,
                      performed_by: Optional[int] = None,
                      comment: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> WorkflowHistory:
        """
        Record a workflow history entry.

        This is the main method for creating audit trail entries.
        """
        history = WorkflowHistory(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            workflow_id=workflow_id,
            from_state_id=from_state_id,
            to_state_id=to_state_id,
            transition_id=transition_id,
            approval_id=approval_id,
            event_type=event_type,
            event_description=event_description,
            comment=comment,
            performed_by=performed_by,
            metadata=metadata,
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_entity_history(self, entity_type: str, entity_id: int,
                          skip: int = 0, limit: int = 100) -> List[WorkflowHistory]:
        """Get workflow history for an entity"""
        return self.db.query(WorkflowHistory).options(
            joinedload(WorkflowHistory.from_state),
            joinedload(WorkflowHistory.to_state)
        ).filter(
            and_(
                WorkflowHistory.entity_type == entity_type,
                WorkflowHistory.entity_id == entity_id
            )
        ).order_by(desc(WorkflowHistory.performed_at)).offset(skip).limit(limit).all()

    def get_workflow_history(self, workflow_id: int,
                            skip: int = 0, limit: int = 100) -> List[WorkflowHistory]:
        """Get all history for a workflow"""
        return self.db.query(WorkflowHistory).filter(
            WorkflowHistory.workflow_id == workflow_id
        ).order_by(desc(WorkflowHistory.performed_at)).offset(skip).limit(limit).all()

    def get_user_activity(self, user_id: int, organization_id: int,
                         skip: int = 0, limit: int = 100) -> List[WorkflowHistory]:
        """Get workflow activity performed by a user"""
        return self.db.query(WorkflowHistory).filter(
            and_(
                WorkflowHistory.organization_id == organization_id,
                WorkflowHistory.performed_by == user_id
            )
        ).order_by(desc(WorkflowHistory.performed_at)).offset(skip).limit(limit).all()

    def get_by_id(self, history_id: int) -> Optional[WorkflowHistory]:
        """Get history entry by ID"""
        return self.db.query(WorkflowHistory).filter(
            WorkflowHistory.id == history_id
        ).first()
