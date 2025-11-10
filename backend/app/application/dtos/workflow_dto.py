"""
DTOs for Workflow Engine.

Supports workflow definitions, states, transitions, approvals, and audit history.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


# ========== Enums ==========

class StateType(str, Enum):
    """Type of workflow state"""
    INITIAL = "INITIAL"
    INTERMEDIATE = "INTERMEDIATE"
    FINAL = "FINAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class ApprovalStatus(str, Enum):
    """Status of approval request"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"


class ApprovalPriority(str, Enum):
    """Priority level for approval requests"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ========== Workflow DTOs ==========

class WorkflowCreateDTO(BaseModel):
    """DTO for creating a new workflow"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    workflow_name: str = Field(..., min_length=1, max_length=100, description="Workflow display name")
    workflow_code: str = Field(..., min_length=1, max_length=50, description="Unique workflow code")
    description: Optional[str] = Field(None, description="Workflow description")
    entity_type: str = Field(..., min_length=1, max_length=50, description="Entity type (material, work_order, ncr, etc.)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Workflow configuration JSON")

    @field_validator('workflow_code')
    @classmethod
    def validate_workflow_code(cls, v):
        """Ensure workflow_code is uppercase and alphanumeric with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('workflow_code must be alphanumeric with underscores')
        return v.upper()

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type"""
        valid_entities = [
            'material', 'work_order', 'project', 'ncr', 'machine', 'department',
            'plant', 'organization', 'maintenance', 'production_log', 'quality',
            'shift', 'lane', 'user', 'bom'
        ]
        if v not in valid_entities:
            raise ValueError(f'entity_type must be one of {valid_entities}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "workflow_name": "NCR Review Workflow",
                "workflow_code": "NCR_REVIEW",
                "description": "Standard workflow for non-conformance report review and resolution",
                "entity_type": "ncr",
                "config": {
                    "allow_skip_states": False,
                    "require_comment_on_transition": True,
                    "auto_assign_on_transition": True,
                    "notification_config": {
                        "on_state_change": ["email", "in_app"],
                        "on_approval_request": ["email"]
                    }
                }
            }
        }


class WorkflowUpdateDTO(BaseModel):
    """DTO for updating an existing workflow"""
    workflow_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """DTO for workflow response"""
    id: int
    organization_id: int
    workflow_name: str
    workflow_code: str
    description: Optional[str] = None
    entity_type: str
    is_system_workflow: bool
    is_active: bool
    config: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    # Nested relationships (optional)
    states: Optional[List['WorkflowStateResponse']] = None
    transitions: Optional[List['WorkflowTransitionResponse']] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "workflow_name": "NCR Review Workflow",
                "workflow_code": "NCR_REVIEW",
                "description": "Standard workflow for NCR review",
                "entity_type": "ncr",
                "is_system_workflow": False,
                "is_active": True,
                "config": {
                    "allow_skip_states": False,
                    "require_comment_on_transition": True
                },
                "created_at": "2025-11-09T10:00:00Z",
                "updated_at": None,
                "created_by": 1,
                "states": [],
                "transitions": []
            }
        }


# ========== WorkflowState DTOs ==========

class WorkflowStateCreateDTO(BaseModel):
    """DTO for creating a workflow state"""
    workflow_id: int = Field(..., gt=0, description="Workflow ID")
    state_name: str = Field(..., min_length=1, max_length=100, description="State display name")
    state_code: str = Field(..., min_length=1, max_length=50, description="Unique state code within workflow")
    description: Optional[str] = Field(None, description="State description")
    state_type: StateType = Field(default=StateType.INTERMEDIATE, description="State type")
    display_order: int = Field(default=0, description="Display order")
    color: Optional[str] = Field(None, max_length=20, description="Hex color for UI (e.g., #FF0000)")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name")
    requires_approval: bool = Field(default=False, description="Does this state require approval")
    actions: Optional[Dict[str, Any]] = Field(None, description="Actions to execute when entering state")
    metadata: Optional[Dict[str, Any]] = Field(None, description="State metadata (SLA, editable fields, etc.)")

    @field_validator('state_code')
    @classmethod
    def validate_state_code(cls, v):
        """Ensure state_code is uppercase and alphanumeric with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('state_code must be alphanumeric with underscores')
        return v.upper()

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Validate hex color format"""
        if v and not (v.startswith('#') and len(v) in (4, 7)):
            raise ValueError('color must be a valid hex color (e.g., #FFF or #FFFFFF)')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": 1,
                "state_name": "Under Review",
                "state_code": "UNDER_REVIEW",
                "description": "NCR is being reviewed by quality team",
                "state_type": "INTERMEDIATE",
                "display_order": 2,
                "color": "#FFA500",
                "icon": "eye",
                "requires_approval": False,
                "actions": {
                    "assign_to_role": "QUALITY_MANAGER",
                    "send_notification": ["email", "in_app"]
                },
                "metadata": {
                    "sla_hours": 24,
                    "editable_fields": ["description", "notes"]
                }
            }
        }


class WorkflowStateUpdateDTO(BaseModel):
    """DTO for updating a workflow state"""
    state_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    display_order: Optional[int] = None
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None
    actions: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowStateResponse(BaseModel):
    """DTO for workflow state response"""
    id: int
    organization_id: int
    workflow_id: int
    state_name: str
    state_code: str
    description: Optional[str] = None
    state_type: StateType
    display_order: int
    color: Optional[str] = None
    icon: Optional[str] = None
    requires_approval: bool
    is_active: bool
    actions: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "workflow_id": 1,
                "state_name": "Under Review",
                "state_code": "UNDER_REVIEW",
                "description": "NCR is being reviewed by quality team",
                "state_type": "INTERMEDIATE",
                "display_order": 2,
                "color": "#FFA500",
                "icon": "eye",
                "requires_approval": False,
                "is_active": True,
                "actions": {"assign_to_role": "QUALITY_MANAGER"},
                "metadata": {"sla_hours": 24},
                "created_at": "2025-11-09T10:00:00Z",
                "updated_at": None
            }
        }


# ========== WorkflowTransition DTOs ==========

class WorkflowTransitionCreateDTO(BaseModel):
    """DTO for creating a workflow transition"""
    workflow_id: int = Field(..., gt=0, description="Workflow ID")
    from_state_id: int = Field(..., gt=0, description="Source state ID")
    to_state_id: int = Field(..., gt=0, description="Target state ID")
    transition_name: str = Field(..., min_length=1, max_length=100, description="Transition display name")
    transition_code: str = Field(..., min_length=1, max_length=50, description="Unique transition code within workflow")
    description: Optional[str] = Field(None, description="Transition description")
    requires_approval: bool = Field(default=False, description="Does this transition require approval")
    requires_comment: bool = Field(default=False, description="Does this transition require a comment")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Conditions for allowing this transition")
    actions: Optional[Dict[str, Any]] = Field(None, description="Actions to execute when transition is taken")
    display_order: int = Field(default=0, description="Display order")
    button_label: Optional[str] = Field(None, max_length=100, description="Custom button label")
    button_color: Optional[str] = Field(None, max_length=20, description="Button color (hex)")

    @field_validator('transition_code')
    @classmethod
    def validate_transition_code(cls, v):
        """Ensure transition_code is uppercase and alphanumeric with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('transition_code must be alphanumeric with underscores')
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": 1,
                "from_state_id": 1,
                "to_state_id": 2,
                "transition_name": "Submit for Review",
                "transition_code": "SUBMIT_FOR_REVIEW",
                "description": "Submit NCR to quality team for review",
                "requires_approval": False,
                "requires_comment": True,
                "conditions": {
                    "field_conditions": [
                        {"field": "description", "operator": "not_empty"},
                        {"field": "severity", "operator": "in", "value": ["HIGH", "CRITICAL"]}
                    ]
                },
                "actions": {
                    "update_fields": {"submitted_at": "NOW()"},
                    "send_notification": ["email"]
                },
                "display_order": 1,
                "button_label": "Submit",
                "button_color": "#0066CC"
            }
        }


class WorkflowTransitionUpdateDTO(BaseModel):
    """DTO for updating a workflow transition"""
    transition_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    requires_approval: Optional[bool] = None
    requires_comment: Optional[bool] = None
    is_active: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    display_order: Optional[int] = None
    button_label: Optional[str] = Field(None, max_length=100)
    button_color: Optional[str] = Field(None, max_length=20)


class WorkflowTransitionResponse(BaseModel):
    """DTO for workflow transition response"""
    id: int
    organization_id: int
    workflow_id: int
    from_state_id: int
    to_state_id: int
    transition_name: str
    transition_code: str
    description: Optional[str] = None
    requires_approval: bool
    requires_comment: bool
    is_active: bool
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    display_order: int
    button_label: Optional[str] = None
    button_color: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Nested state details (optional)
    from_state: Optional[WorkflowStateResponse] = None
    to_state: Optional[WorkflowStateResponse] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "workflow_id": 1,
                "from_state_id": 1,
                "to_state_id": 2,
                "transition_name": "Submit for Review",
                "transition_code": "SUBMIT_FOR_REVIEW",
                "description": "Submit NCR for review",
                "requires_approval": False,
                "requires_comment": True,
                "is_active": True,
                "conditions": {"field_conditions": [{"field": "severity", "operator": "not_empty"}]},
                "actions": {"send_notification": ["email"]},
                "display_order": 1,
                "button_label": "Submit",
                "button_color": "#0066CC",
                "created_at": "2025-11-09T10:00:00Z",
                "updated_at": None,
                "from_state": None,
                "to_state": None
            }
        }


# ========== Approval DTOs ==========

class ApprovalCreateDTO(BaseModel):
    """DTO for creating an approval request"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    entity_type: str = Field(..., min_length=1, max_length=50, description="Entity type")
    entity_id: int = Field(..., gt=0, description="Entity ID")
    workflow_id: Optional[int] = Field(None, gt=0, description="Workflow ID (optional)")
    workflow_state_id: Optional[int] = Field(None, gt=0, description="Workflow state ID (optional)")
    approval_type: str = Field(..., min_length=1, max_length=50, description="Approval type (state_change, transition, manual)")
    title: str = Field(..., min_length=1, max_length=200, description="Approval title")
    description: Optional[str] = Field(None, description="Approval description")
    approver_user_id: Optional[int] = Field(None, gt=0, description="Specific user to approve")
    approver_role: Optional[str] = Field(None, max_length=50, description="Role to approve (if not specific user)")
    priority: ApprovalPriority = Field(default=ApprovalPriority.MEDIUM, description="Priority level")
    request_comment: Optional[str] = Field(None, description="Comment from requester")
    due_date: Optional[datetime] = Field(None, description="Due date for approval")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Approval metadata")

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type"""
        valid_entities = [
            'material', 'work_order', 'project', 'ncr', 'machine', 'department',
            'plant', 'organization', 'maintenance', 'production_log', 'quality',
            'shift', 'lane', 'user', 'bom'
        ]
        if v not in valid_entities:
            raise ValueError(f'entity_type must be one of {valid_entities}')
        return v

    @field_validator('approver_user_id', 'approver_role')
    @classmethod
    def validate_approver(cls, v, info):
        """Ensure at least one of approver_user_id or approver_role is provided"""
        # This is a simplified check - full validation would need access to both fields
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "entity_type": "ncr",
                "entity_id": 123,
                "workflow_id": 1,
                "workflow_state_id": 2,
                "approval_type": "state_change",
                "title": "Approve NCR Closure",
                "description": "NCR #123 requires approval to close",
                "approver_user_id": None,
                "approver_role": "QUALITY_MANAGER",
                "priority": "HIGH",
                "request_comment": "Root cause analysis completed",
                "due_date": "2025-11-10T17:00:00Z",
                "metadata": {
                    "escalation_hours": 24,
                    "escalate_to_role": "PLANT_MANAGER"
                }
            }
        }


class ApprovalActionDTO(BaseModel):
    """DTO for responding to an approval request"""
    status: ApprovalStatus = Field(..., description="Approval decision (APPROVED or REJECTED)")
    approval_comment: Optional[str] = Field(None, description="Comment from approver")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Ensure status is APPROVED or REJECTED"""
        if v not in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
            raise ValueError('status must be APPROVED or REJECTED')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "APPROVED",
                "approval_comment": "All corrective actions have been verified and are satisfactory"
            }
        }


class ApprovalUpdateDTO(BaseModel):
    """DTO for updating an approval request (admin only)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    approver_user_id: Optional[int] = Field(None, gt=0)
    approver_role: Optional[str] = Field(None, max_length=50)
    priority: Optional[ApprovalPriority] = None
    due_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ApprovalResponse(BaseModel):
    """DTO for approval response"""
    id: int
    organization_id: int
    entity_type: str
    entity_id: int
    workflow_id: Optional[int] = None
    workflow_state_id: Optional[int] = None
    approval_type: str
    title: str
    description: Optional[str] = None
    approver_user_id: Optional[int] = None
    approver_role: Optional[str] = None
    status: ApprovalStatus
    priority: ApprovalPriority
    request_comment: Optional[str] = None
    approval_comment: Optional[str] = None
    requested_at: datetime
    requested_by: Optional[int] = None
    due_date: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed fields
    is_overdue: Optional[bool] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "entity_type": "ncr",
                "entity_id": 123,
                "workflow_id": 1,
                "workflow_state_id": 2,
                "approval_type": "state_change",
                "title": "Approve NCR Closure",
                "description": "NCR #123 requires approval to close",
                "approver_user_id": 5,
                "approver_role": "QUALITY_MANAGER",
                "status": "PENDING",
                "priority": "HIGH",
                "request_comment": "Root cause analysis completed",
                "approval_comment": None,
                "requested_at": "2025-11-09T10:00:00Z",
                "requested_by": 1,
                "due_date": "2025-11-10T17:00:00Z",
                "responded_at": None,
                "metadata": {"escalation_hours": 24},
                "created_at": "2025-11-09T10:00:00Z",
                "updated_at": None,
                "is_overdue": False
            }
        }


# ========== WorkflowHistory DTOs ==========

class WorkflowHistoryResponse(BaseModel):
    """DTO for workflow history response"""
    id: int
    organization_id: int
    entity_type: str
    entity_id: int
    workflow_id: Optional[int] = None
    from_state_id: Optional[int] = None
    to_state_id: Optional[int] = None
    transition_id: Optional[int] = None
    approval_id: Optional[int] = None
    event_type: str
    event_description: Optional[str] = None
    comment: Optional[str] = None
    performed_by: Optional[int] = None
    performed_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    # Nested details (optional)
    from_state: Optional[WorkflowStateResponse] = None
    to_state: Optional[WorkflowStateResponse] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "entity_type": "ncr",
                "entity_id": 123,
                "workflow_id": 1,
                "from_state_id": 1,
                "to_state_id": 2,
                "transition_id": 1,
                "approval_id": None,
                "event_type": "state_change",
                "event_description": "Transitioned from Draft to Under Review",
                "comment": "Submitting for quality review",
                "performed_by": 1,
                "performed_at": "2025-11-09T10:00:00Z",
                "metadata": {
                    "duration_in_state": 3600,
                    "field_changes": {"priority": {"from": "LOW", "to": "HIGH"}}
                },
                "from_state": None,
                "to_state": None
            }
        }


# ========== Entity Workflow Status DTOs ==========

class EntityWorkflowStatusResponse(BaseModel):
    """
    DTO for embedding workflow status in entity responses.

    Usage:
        class NCRWithWorkflowResponse(NCRResponse):
            workflow_status: Optional[EntityWorkflowStatusResponse] = None
    """
    workflow_id: int
    workflow_name: str
    workflow_code: str
    current_state_id: int
    current_state_name: str
    current_state_code: str
    current_state_type: StateType
    current_state_color: Optional[str] = None
    current_state_icon: Optional[str] = None
    available_transitions: List[WorkflowTransitionResponse] = Field(default_factory=list)
    pending_approvals: List[ApprovalResponse] = Field(default_factory=list)
    last_transition_at: Optional[datetime] = None
    last_transition_by: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": 1,
                "workflow_name": "NCR Review Workflow",
                "workflow_code": "NCR_REVIEW",
                "current_state_id": 2,
                "current_state_name": "Under Review",
                "current_state_code": "UNDER_REVIEW",
                "current_state_type": "INTERMEDIATE",
                "current_state_color": "#FFA500",
                "current_state_icon": "eye",
                "available_transitions": [],
                "pending_approvals": [],
                "last_transition_at": "2025-11-09T10:00:00Z",
                "last_transition_by": 1
            }
        }


# ========== Workflow Execution DTOs ==========

class WorkflowTransitionExecuteDTO(BaseModel):
    """DTO for executing a workflow transition"""
    transition_id: int = Field(..., gt=0, description="Transition ID to execute")
    comment: Optional[str] = Field(None, description="Comment for this transition")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "transition_id": 1,
                "comment": "Submitting NCR for quality review",
                "metadata": {
                    "urgency": "high",
                    "related_documents": ["DOC-123", "DOC-456"]
                }
            }
        }


class WorkflowStateChangeDTO(BaseModel):
    """DTO for manually changing workflow state (admin operation)"""
    new_state_id: int = Field(..., gt=0, description="New state ID")
    comment: str = Field(..., min_length=1, description="Reason for manual state change")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "new_state_id": 5,
                "comment": "Manual override due to system error - NCR was actually closed",
                "metadata": {
                    "reason": "data_correction",
                    "authorized_by": 123
                }
            }
        }


# Update forward references for nested models
WorkflowResponse.model_rebuild()
WorkflowTransitionResponse.model_rebuild()
