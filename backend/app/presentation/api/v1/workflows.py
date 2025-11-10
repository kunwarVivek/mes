"""
API endpoints for Workflow Engine

Provides state machine, approval workflows, and audit trail management
for any entity type (NCR, work orders, materials, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.services.workflow_service import WorkflowService
from app.application.dtos.workflow_dto import (
    WorkflowCreateDTO,
    WorkflowUpdateDTO,
    WorkflowResponse,
    WorkflowStateCreateDTO,
    WorkflowStateUpdateDTO,
    WorkflowStateResponse,
    WorkflowTransitionCreateDTO,
    WorkflowTransitionUpdateDTO,
    WorkflowTransitionResponse,
    ApprovalCreateDTO,
    ApprovalActionDTO,
    ApprovalUpdateDTO,
    ApprovalResponse,
    WorkflowHistoryResponse,
    WorkflowTransitionExecuteDTO,
    StateType,
    ApprovalStatus,
)

router = APIRouter(prefix="/workflows", tags=["workflow-engine"])


# ========== Workflow Management Endpoints ==========

@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    dto: WorkflowCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new workflow definition.

    **Workflows** define the state machine for entities (NCR, work orders, etc.)

    **Entity Types:**
    - material, work_order, project, ncr, machine, department, etc.

    **Features:**
    - Custom states with colors, icons, and actions
    - Conditional transitions with approval requirements
    - Automated actions on state changes
    - Audit trail for all state changes

    **Requires:** Admin or workflow configuration permission
    """
    service = WorkflowService(db)
    created_by = current_user.get("id")

    try:
        workflow = service.workflow_repo.create(
            organization_id=dto.organization_id,
            workflow_name=dto.workflow_name,
            workflow_code=dto.workflow_code,
            entity_type=dto.entity_type,
            description=dto.description,
            config=dto.config,
            created_by=created_by
        )
        return WorkflowResponse.model_validate(workflow)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    include_inactive: bool = Query(False, description="Include inactive workflows"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all workflows for current organization.

    **Query Params:**
    - entity_type: Filter by entity type (ncr, work_order, etc.)
    - include_inactive: Include inactive workflows
    - skip: Pagination offset
    - limit: Max results (1-500)

    **Returns:** List of workflows with their metadata
    """
    service = WorkflowService(db)
    organization_id = current_user.get("organization_id")

    workflows = service.workflow_repo.list_workflows(
        organization_id=organization_id,
        entity_type=entity_type,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit
    )
    return [WorkflowResponse.model_validate(w) for w in workflows]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int = Path(..., gt=0, description="Workflow ID"),
    include_states: bool = Query(False, description="Include states and transitions"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get workflow details by ID.

    **Query Params:**
    - include_states: Include states and transitions in response

    **Returns:** Workflow with optional nested states/transitions
    """
    service = WorkflowService(db)

    if include_states:
        workflow = service.get_workflow_with_details(workflow_id)
    else:
        workflow = service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    return WorkflowResponse.model_validate(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int = Path(..., gt=0, description="Workflow ID"),
    dto: WorkflowUpdateDTO = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a workflow definition.

    **Note:**
    - Cannot update workflow_code or entity_type
    - System workflows cannot be modified

    **Requires:** Admin or workflow configuration permission
    """
    service = WorkflowService(db)

    try:
        # Filter out None values
        updates = {k: v for k, v in dto.model_dump().items() if v is not None}

        workflow = service.workflow_repo.update(workflow_id, updates)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )

        return WorkflowResponse.model_validate(workflow)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int = Path(..., gt=0, description="Workflow ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a workflow definition.

    **Warning:**
    - System workflows cannot be deleted
    - This cascades to delete states, transitions, and history
    - Entities using this workflow will need a new workflow assigned

    **Requires:** Admin or workflow configuration permission
    """
    service = WorkflowService(db)

    try:
        success = service.workflow_repo.delete(workflow_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/entity/{entity_type}/default", response_model=WorkflowResponse)
async def get_default_workflow(
    entity_type: str = Path(..., description="Entity type (ncr, work_order, etc.)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the default workflow for an entity type.

    **Use Case:**
    When creating a new entity (NCR, work order, etc.), use this endpoint
    to get the workflow and initial state to assign.

    **Example:** GET /workflows/entity/ncr/default
    Returns the default NCR workflow with initial state
    """
    service = WorkflowService(db)
    organization_id = current_user.get("organization_id")

    workflow = service.get_workflow_for_entity(organization_id, entity_type)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No default workflow found for entity type '{entity_type}'"
        )

    return WorkflowResponse.model_validate(workflow)


# ========== State Management Endpoints ==========

@router.post("/{workflow_id}/states", response_model=WorkflowStateResponse,
            status_code=status.HTTP_201_CREATED)
async def add_state(
    workflow_id: int = Path(..., gt=0, description="Workflow ID"),
    dto: WorkflowStateCreateDTO = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a state to a workflow.

    **State Types:**
    - INITIAL: Starting state (only one per workflow)
    - INTERMEDIATE: In-progress states
    - FINAL: Completed successfully
    - CANCELLED: Cancelled/abandoned
    - REJECTED: Rejected/failed

    **State Features:**
    - Color and icon for UI display
    - Approval requirements
    - Entry actions (notifications, assignments, etc.)
    - SLA tracking metadata
    - Custom field validation rules

    **Example Actions:**
    ```json
    {
      "assign_to_role": "QUALITY_MANAGER",
      "send_notification": ["email", "in_app"],
      "update_fields": {"priority": "high"}
    }
    ```
    """
    service = WorkflowService(db)
    organization_id = current_user.get("organization_id")

    # Override workflow_id from path
    dto.workflow_id = workflow_id

    try:
        state = service.state_repo.create(
            organization_id=organization_id,
            workflow_id=dto.workflow_id,
            state_name=dto.state_name,
            state_code=dto.state_code,
            state_type=dto.state_type,
            description=dto.description,
            display_order=dto.display_order,
            color=dto.color,
            icon=dto.icon,
            requires_approval=dto.requires_approval,
            actions=dto.actions,
            metadata=dto.metadata
        )
        return WorkflowStateResponse.model_validate(state)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{workflow_id}/states", response_model=List[WorkflowStateResponse])
async def list_states(
    workflow_id: int = Path(..., gt=0, description="Workflow ID"),
    include_inactive: bool = Query(False, description="Include inactive states"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all states for a workflow.

    **Returns:** States ordered by display_order
    """
    service = WorkflowService(db)

    states = service.state_repo.list_by_workflow(workflow_id, include_inactive)
    return [WorkflowStateResponse.model_validate(s) for s in states]


@router.put("/states/{state_id}", response_model=WorkflowStateResponse)
async def update_state(
    state_id: int = Path(..., gt=0, description="State ID"),
    dto: WorkflowStateUpdateDTO = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a workflow state.

    **Note:** Cannot change state_code or state_type after creation
    """
    service = WorkflowService(db)

    try:
        updates = {k: v for k, v in dto.model_dump().items() if v is not None}

        state = service.state_repo.update(state_id, updates)
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"State {state_id} not found"
            )

        return WorkflowStateResponse.model_validate(state)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/states/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_state(
    state_id: int = Path(..., gt=0, description="State ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a workflow state.

    **Warning:** This cascades to delete transitions to/from this state
    """
    service = WorkflowService(db)

    success = service.state_repo.delete(state_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State {state_id} not found"
        )


# ========== Transition Management Endpoints ==========

@router.post("/{workflow_id}/transitions", response_model=WorkflowTransitionResponse,
            status_code=status.HTTP_201_CREATED)
async def add_transition(
    workflow_id: int = Path(..., gt=0, description="Workflow ID"),
    dto: WorkflowTransitionCreateDTO = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a transition between states.

    **Transitions** define the allowed paths between states.

    **Features:**
    - **Conditional logic:** Role requirements, field validations, custom conditions
    - **Approval workflows:** Optional approval before state change
    - **Actions:** Send notifications, update fields, create tasks
    - **Comment requirements:** Enforce comments for audit trail

    **Example Conditions:**
    ```json
    {
      "required_roles": ["QUALITY_MANAGER"],
      "required_fields": ["root_cause", "corrective_action"],
      "custom_conditions": [
        {"field": "severity", "operator": "in", "value": ["HIGH", "CRITICAL"]}
      ]
    }
    ```

    **Example Actions:**
    ```json
    {
      "pre_actions": [{"action": "send_notification", "params": {"to": "quality_team"}}],
      "post_actions": [{"action": "assign_to", "params": {"role": "PRODUCTION_MANAGER"}}]
    }
    ```
    """
    service = WorkflowService(db)
    organization_id = current_user.get("organization_id")

    # Override workflow_id from path
    dto.workflow_id = workflow_id

    try:
        transition = service.transition_repo.create(
            organization_id=organization_id,
            workflow_id=dto.workflow_id,
            from_state_id=dto.from_state_id,
            to_state_id=dto.to_state_id,
            transition_name=dto.transition_name,
            transition_code=dto.transition_code,
            description=dto.description,
            requires_approval=dto.requires_approval,
            requires_comment=dto.requires_comment,
            conditions=dto.conditions,
            actions=dto.actions,
            display_order=dto.display_order
        )
        return WorkflowTransitionResponse.model_validate(transition)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{workflow_id}/transitions", response_model=List[WorkflowTransitionResponse])
async def list_transitions(
    workflow_id: int = Path(..., gt=0, description="Workflow ID"),
    include_inactive: bool = Query(False, description="Include inactive transitions"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all transitions for a workflow.

    **Returns:** All transitions with from/to state details
    """
    service = WorkflowService(db)

    transitions = service.transition_repo.list_by_workflow(workflow_id, include_inactive)
    return [WorkflowTransitionResponse.model_validate(t) for t in transitions]


@router.put("/transitions/{transition_id}", response_model=WorkflowTransitionResponse)
async def update_transition(
    transition_id: int = Path(..., gt=0, description="Transition ID"),
    dto: WorkflowTransitionUpdateDTO = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a workflow transition.

    **Note:** Cannot change from_state_id or to_state_id after creation
    """
    service = WorkflowService(db)

    try:
        updates = {k: v for k, v in dto.model_dump().items() if v is not None}

        transition = service.transition_repo.update(transition_id, updates)
        if not transition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transition {transition_id} not found"
            )

        return WorkflowTransitionResponse.model_validate(transition)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/transitions/{transition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transition(
    transition_id: int = Path(..., gt=0, description="Transition ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a workflow transition.

    **Note:** This prevents users from taking this transition path
    """
    service = WorkflowService(db)

    success = service.transition_repo.delete(transition_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transition {transition_id} not found"
        )


# ========== Workflow Execution Endpoints ==========

@router.post("/execute-transition")
async def execute_transition(
    entity_type: str = Query(..., description="Entity type (ncr, work_order, etc.)"),
    entity_id: int = Query(..., gt=0, description="Entity ID"),
    transition_id: int = Query(..., gt=0, description="Transition ID to execute"),
    comment: Optional[str] = Query(None, description="Optional comment"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Execute a workflow state transition.

    **This is the core workflow engine endpoint.**

    **Process:**
    1. Validates transition is allowed (conditions, roles, required fields)
    2. Checks if comments are required
    3. Executes pre-transition actions
    4. Creates approval if required (transition pauses)
    5. Changes state (if no approval needed)
    6. Executes post-transition and state-entry actions
    7. Records audit trail

    **Request:**
    - entity_type: Type of entity (ncr, work_order, etc.)
    - entity_id: ID of the entity
    - transition_id: Transition to execute
    - comment: Optional comment for audit trail

    **Response:**
    ```json
    {
      "success": true,
      "message": "Transitioned to Under Review",
      "new_state": {
        "id": 2,
        "code": "UNDER_REVIEW",
        "name": "Under Review"
      },
      "requires_approval": false
    }
    ```

    **Errors:**
    - 400: Transition not allowed (conditions not met)
    - 403: User lacks required role
    - 404: Transition or entity not found
    """
    service = WorkflowService(db)
    actor_id = current_user.get("id")
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])

    # TODO: Fetch entity data for condition evaluation
    # This would need to be implemented per entity type
    entity_data = {}

    success, error_msg, new_state = service.execute_transition(
        entity_type=entity_type,
        entity_id=entity_id,
        transition_id=transition_id,
        actor_id=actor_id,
        entity_data=entity_data,
        user_roles=user_roles,
        comments=comment,
        organization_id=organization_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    return {
        "success": True,
        "message": error_msg or f"Transitioned to {new_state.state_name}",
        "new_state": {
            "id": new_state.id,
            "code": new_state.state_code,
            "name": new_state.state_name,
            "type": new_state.state_type.value,
            "color": new_state.color,
            "icon": new_state.icon,
        } if new_state else None,
        "requires_approval": "pending approval" in (error_msg or "").lower()
    }


@router.get("/entity/{entity_type}/{entity_id}/status")
async def get_workflow_status(
    entity_type: str = Path(..., description="Entity type (ncr, work_order, etc.)"),
    entity_id: int = Path(..., gt=0, description="Entity ID"),
    current_state_id: int = Query(..., gt=0, description="Current state ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete workflow status for an entity.

    **Returns:**
    - Current state details
    - Available transitions (filtered by user roles and conditions)
    - Pending approvals
    - Last transition info

    **Use Case:**
    Frontend calls this to display:
    - Current state badge/indicator
    - Available action buttons
    - Pending approval notices

    **Example Response:**
    ```json
    {
      "current_state": {
        "id": 2,
        "code": "UNDER_REVIEW",
        "name": "Under Review",
        "type": "INTERMEDIATE",
        "color": "#FFA500",
        "icon": "eye"
      },
      "available_transitions": [
        {
          "id": 1,
          "code": "APPROVE",
          "name": "Approve",
          "to_state": {"id": 3, "code": "APPROVED", "name": "Approved"},
          "requires_approval": false,
          "requires_comment": true
        }
      ],
      "pending_approvals": []
    }
    ```
    """
    service = WorkflowService(db)
    user_roles = current_user.get("roles", [])

    # TODO: Fetch entity data for condition evaluation
    entity_data = {}

    status_info = service.get_entity_workflow_status(
        entity_type=entity_type,
        entity_id=entity_id,
        current_state_id=current_state_id,
        entity_data=entity_data,
        user_roles=user_roles
    )

    return status_info


@router.get("/entity/{entity_type}/{entity_id}/history",
           response_model=List[WorkflowHistoryResponse])
async def get_workflow_history(
    entity_type: str = Path(..., description="Entity type (ncr, work_order, etc.)"),
    entity_id: int = Path(..., gt=0, description="Entity ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete audit trail for an entity's workflow.

    **Returns:** Chronological list of:
    - State transitions
    - Approval requests/responses
    - Comments
    - System events

    **Use Case:**
    Display activity timeline showing:
    - Who changed state and when
    - Why (comments)
    - What changed (from state → to state)
    - Approval history

    **Example:**
    ```json
    [
      {
        "id": 1,
        "event_type": "transition",
        "event_description": "Transitioned from Draft to Under Review",
        "from_state": {"id": 1, "name": "Draft"},
        "to_state": {"id": 2, "name": "Under Review"},
        "performed_by": 5,
        "performed_at": "2025-11-09T10:00:00Z",
        "comment": "Submitting for quality review"
      }
    ]
    ```
    """
    service = WorkflowService(db)

    history = service.get_entity_history(entity_type, entity_id, skip, limit)
    return [WorkflowHistoryResponse.model_validate(h) for h in history]


# ========== Approval Management Endpoints ==========

@router.post("/approvals/request", response_model=ApprovalResponse,
            status_code=status.HTTP_201_CREATED)
async def request_approval(
    dto: ApprovalCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a manual approval request.

    **Use Cases:**
    - Manual approvals outside of workflow transitions
    - Document approvals
    - Change request approvals
    - Override approvals

    **Approval Types:**
    - transition: Approval for workflow transition
    - state_change: Approval for state change
    - manual: Manual approval request

    **Approver Assignment:**
    - approver_user_id: Specific user to approve
    - approver_role: Any user with this role can approve
    - At least one must be specified

    **Priority Levels:**
    - LOW: Standard approval (5+ days)
    - MEDIUM: Normal approval (2-3 days)
    - HIGH: Urgent approval (24 hours)
    - CRITICAL: Immediate approval (same day)
    """
    service = WorkflowService(db)
    requested_by = current_user.get("id")

    try:
        approval = service.approval_repo.create(
            organization_id=dto.organization_id,
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            workflow_id=dto.workflow_id,
            workflow_state_id=dto.workflow_state_id,
            approval_type=dto.approval_type,
            title=dto.title,
            description=dto.description,
            approver_user_id=dto.approver_user_id,
            approver_role=dto.approver_role,
            priority=dto.priority,
            request_comment=dto.request_comment,
            requested_by=requested_by,
            due_date=dto.due_date,
            metadata=dto.metadata
        )
        return ApprovalResponse.model_validate(approval)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/approvals/{approval_id}/approve")
async def approve_approval(
    approval_id: int = Path(..., gt=0, description="Approval ID"),
    action: ApprovalActionDTO = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Approve an approval request.

    **Process:**
    1. Validates approver has permission
    2. Marks approval as APPROVED
    3. Executes pending workflow transition (if applicable)
    4. Records approval in audit trail
    5. Sends notifications

    **Request:**
    ```json
    {
      "status": "APPROVED",
      "approval_comment": "All corrective actions verified"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "message": "Approval granted",
      "new_state": {
        "id": 3,
        "code": "APPROVED",
        "name": "Approved"
      }
    }
    ```
    """
    service = WorkflowService(db)
    approver_id = current_user.get("id")

    success, error_msg, new_state = service.process_approval(
        approval_id=approval_id,
        approver_id=approver_id,
        approved=True,
        comments=action.approval_comment if action else None,
        entity_data={}
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    return {
        "success": True,
        "message": "Approval granted",
        "new_state": {
            "id": new_state.id,
            "code": new_state.state_code,
            "name": new_state.state_name,
        } if new_state else None
    }


@router.post("/approvals/{approval_id}/reject")
async def reject_approval(
    approval_id: int = Path(..., gt=0, description="Approval ID"),
    action: ApprovalActionDTO = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Reject an approval request.

    **Process:**
    1. Validates approver has permission
    2. Marks approval as REJECTED
    3. Records rejection in audit trail
    4. Sends notifications
    5. Entity remains in current state

    **Request:**
    ```json
    {
      "status": "REJECTED",
      "approval_comment": "Corrective actions insufficient, needs revision"
    }
    ```
    """
    service = WorkflowService(db)
    approver_id = current_user.get("id")

    success, error_msg, _ = service.process_approval(
        approval_id=approval_id,
        approver_id=approver_id,
        approved=False,
        comments=action.approval_comment if action else None,
        entity_data={}
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    return {
        "success": True,
        "message": "Approval rejected"
    }


@router.get("/approvals/pending", response_model=List[ApprovalResponse])
async def get_pending_approvals(
    include_role_approvals: bool = Query(True, description="Include approvals for user's roles"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all pending approvals for current user.

    **Returns:** Approvals assigned to:
    - User specifically (approver_user_id)
    - User's roles (approver_role) - if include_role_approvals=true

    **Sorting:** By priority (descending), then due date (ascending)

    **Use Case:**
    - User's "My Approvals" inbox
    - Approval notification count
    - Dashboard widgets
    """
    service = WorkflowService(db)
    user_id = current_user.get("id")
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])

    # Get user-specific approvals
    approvals = service.get_pending_approvals(user_id, organization_id)

    # Get role-based approvals
    if include_role_approvals:
        for role in user_roles:
            role_approvals = service.get_pending_approvals_by_role(role, organization_id)
            approvals.extend(role_approvals)

    # Remove duplicates and sort
    unique_approvals = {a.id: a for a in approvals}.values()
    sorted_approvals = sorted(
        unique_approvals,
        key=lambda a: (
            -a.priority.value if hasattr(a.priority, 'value') else 0,
            a.due_date or datetime.max
        )
    )

    return [ApprovalResponse.model_validate(a) for a in sorted_approvals]


@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval_details(
    approval_id: int = Path(..., gt=0, description="Approval ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get approval details by ID.

    **Returns:** Full approval information including:
    - Request details
    - Entity information
    - Workflow state
    - Comments
    - Status and timestamps
    """
    service = WorkflowService(db)

    approval = service.approval_repo.get_by_id(approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    return ApprovalResponse.model_validate(approval)
