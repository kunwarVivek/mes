"""
DTOs for Project Management (Documents, Milestones, RDA, BOM)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from decimal import Decimal


# ========== Project Document DTOs ==========

class ProjectDocumentCreateDTO(BaseModel):
    """DTO for creating a project document"""
    project_id: int = Field(..., gt=0, description="Project ID")
    organization_id: int = Field(..., gt=0, description="Organization ID")
    document_name: str = Field(..., min_length=1, max_length=200, description="Document name")
    document_code: str = Field(..., min_length=1, max_length=100, description="Document code")
    description: Optional[str] = Field(None, description="Document description")
    document_type: str = Field(..., description="Document type (DRAWING, SPEC, etc.)")
    category: Optional[str] = Field(None, max_length=100, description="Category")
    version: str = Field(..., min_length=1, max_length=50, description="Version")
    file_path: str = Field(..., min_length=1, max_length=500, description="File path")
    file_name: str = Field(..., min_length=1, max_length=255, description="File name")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, max_length=100, description="MIME type")
    checksum: Optional[str] = Field(None, max_length=64, description="SHA-256 checksum")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    is_public: bool = Field(default=False, description="Is document public")
    requires_approval: bool = Field(default=False, description="Requires approval")

    @field_validator('document_type')
    @classmethod
    def validate_document_type(cls, v):
        """Validate document type"""
        valid_types = ['DRAWING', 'SPEC', 'REPORT', 'CONTRACT', 'PROCEDURE', 'MANUAL', 'OTHER']
        if v not in valid_types:
            raise ValueError(f'document_type must be one of {valid_types}')
        return v


class ProjectDocumentUpdateDTO(BaseModel):
    """DTO for updating a project document"""
    document_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    approval_status: Optional[str] = None
    is_archived: Optional[bool] = None


class ProjectDocumentResponse(BaseModel):
    """DTO for project document response"""
    id: int
    organization_id: int
    project_id: int
    document_name: str
    document_code: str
    description: Optional[str]
    document_type: str
    category: Optional[str]
    version: str
    revision: int
    is_latest_version: bool
    parent_document_id: Optional[int]
    file_path: str
    file_name: str
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    checksum: Optional[str]
    tags: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    uploaded_by: int
    is_public: bool
    requires_approval: bool
    approval_status: Optional[str]
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime]
    archived_at: Optional[datetime]

    class Config:
        from_attributes = True


# ========== Project Milestone DTOs ==========

class ProjectMilestoneCreateDTO(BaseModel):
    """DTO for creating a project milestone"""
    project_id: int = Field(..., gt=0, description="Project ID")
    organization_id: int = Field(..., gt=0, description="Organization ID")
    milestone_name: str = Field(..., min_length=1, max_length=200, description="Milestone name")
    milestone_code: str = Field(..., min_length=1, max_length=100, description="Milestone code")
    description: Optional[str] = Field(None, description="Description")
    milestone_type: str = Field(..., description="Milestone type (DESIGN, PROCUREMENT, etc.)")
    planned_date: date = Field(..., description="Planned date")
    baseline_date: Optional[date] = Field(None, description="Baseline date")
    is_critical_path: bool = Field(default=False, description="Is critical path")
    dependencies: Optional[List[int]] = Field(None, description="Dependent milestone IDs")
    deliverables: Optional[List[Dict[str, Any]]] = Field(None, description="Deliverables")
    owner_user_id: Optional[int] = Field(None, description="Owner user ID")
    assigned_team: Optional[str] = Field(None, max_length=100, description="Assigned team")
    alert_days_before: Optional[int] = Field(None, description="Alert days before due")
    alert_recipients: Optional[List[str]] = Field(None, description="Alert recipients")
    notes: Optional[str] = Field(None, description="Notes")
    display_order: int = Field(default=0, description="Display order")

    @field_validator('milestone_code')
    @classmethod
    def validate_milestone_code(cls, v):
        """Ensure milestone_code is uppercase"""
        return v.upper()


class ProjectMilestoneUpdateDTO(BaseModel):
    """DTO for updating a project milestone"""
    milestone_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    planned_date: Optional[date] = None
    baseline_date: Optional[date] = None
    actual_date: Optional[date] = None
    is_critical_path: Optional[bool] = None
    status: Optional[str] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    dependencies: Optional[List[int]] = None
    deliverables: Optional[List[Dict[str, Any]]] = None
    owner_user_id: Optional[int] = None
    assigned_team: Optional[str] = None
    alert_days_before: Optional[int] = None
    alert_recipients: Optional[List[str]] = None
    notes: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class ProjectMilestoneResponse(BaseModel):
    """DTO for project milestone response"""
    id: int
    organization_id: int
    project_id: int
    milestone_name: str
    milestone_code: str
    description: Optional[str]
    milestone_type: str
    planned_date: date
    baseline_date: Optional[date]
    actual_date: Optional[date]
    is_critical_path: bool
    status: str
    completion_percentage: int
    dependencies: Optional[List[int]]
    deliverables: Optional[List[Dict[str, Any]]]
    owner_user_id: Optional[int]
    assigned_team: Optional[str]
    alert_days_before: Optional[int]
    alert_recipients: Optional[List[str]]
    notes: Optional[str]
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ========== RDA Drawing DTOs ==========

class RDADrawingCreateDTO(BaseModel):
    """DTO for creating an RDA (Request for Drawing Approval)"""
    project_id: int = Field(..., gt=0, description="Project ID")
    organization_id: int = Field(..., gt=0, description="Organization ID")
    document_id: Optional[int] = Field(None, description="Associated document ID")
    rda_number: str = Field(..., min_length=1, max_length=100, description="RDA number")
    drawing_number: str = Field(..., min_length=1, max_length=100, description="Drawing number")
    drawing_title: str = Field(..., min_length=1, max_length=200, description="Drawing title")
    revision: str = Field(..., min_length=1, max_length=50, description="Revision")
    description: Optional[str] = Field(None, description="Description")
    workflow_id: Optional[int] = Field(None, description="Workflow ID")
    required_approval_date: Optional[date] = Field(None, description="Required approval date")
    priority: str = Field(default='NORMAL', description="Priority (LOW, NORMAL, HIGH, URGENT)")
    distribution_list: Optional[List[str]] = Field(None, description="Distribution list")
    notify_on_approval: bool = Field(default=True, description="Notify on approval")

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority"""
        valid_priorities = ['LOW', 'NORMAL', 'HIGH', 'URGENT']
        if v not in valid_priorities:
            raise ValueError(f'priority must be one of {valid_priorities}')
        return v


class RDADrawingUpdateDTO(BaseModel):
    """DTO for updating an RDA drawing"""
    drawing_title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    required_approval_date: Optional[date] = None
    priority: Optional[str] = None
    distribution_list: Optional[List[str]] = None
    notify_on_approval: Optional[bool] = None


class RDADrawingSubmitDTO(BaseModel):
    """DTO for submitting an RDA for approval"""
    approvers: List[Dict[str, Any]] = Field(..., description="List of approvers with roles")

    class Config:
        json_schema_extra = {
            "example": {
                "approvers": [
                    {"user_id": 123, "role": "Design Lead"},
                    {"user_id": 456, "role": "Project Manager"}
                ]
            }
        }


class RDADrawingReviewDTO(BaseModel):
    """DTO for reviewing an RDA drawing"""
    status: str = Field(..., description="Approval status (APPROVED, REJECTED)")
    comments: Optional[str] = Field(None, description="Review comments")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status"""
        valid_statuses = ['APPROVED', 'REJECTED']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v


class RDADrawingResponse(BaseModel):
    """DTO for RDA drawing response"""
    id: int
    organization_id: int
    project_id: int
    document_id: Optional[int]
    rda_number: str
    drawing_number: str
    drawing_title: str
    revision: str
    description: Optional[str]
    workflow_id: Optional[int]
    current_workflow_state_id: Optional[int]
    approval_status: str
    submitted_by: int
    submitted_date: Optional[datetime]
    required_approval_date: Optional[date]
    priority: str
    approvers: Optional[List[Dict[str, Any]]]
    review_comments: Optional[List[Dict[str, Any]]]
    approved_date: Optional[datetime]
    approved_by: Optional[int]
    rejection_reason: Optional[str]
    rejection_date: Optional[datetime]
    distribution_list: Optional[List[str]]
    notify_on_approval: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ========== Project BOM DTOs ==========

class ProjectBOMCreateDTO(BaseModel):
    """DTO for creating a project BOM item"""
    project_id: int = Field(..., gt=0, description="Project ID")
    organization_id: int = Field(..., gt=0, description="Organization ID")
    bom_code: str = Field(..., min_length=1, max_length=100, description="BOM code")
    description: Optional[str] = Field(None, description="Description")
    bom_type: str = Field(..., description="BOM type (PROJECT_BOM, ASSEMBLY_BOM, PROCUREMENT_BOM)")
    material_id: Optional[int] = Field(None, description="Material ID")
    part_number: Optional[str] = Field(None, max_length=100, description="Part number")
    part_description: Optional[str] = Field(None, max_length=500, description="Part description")
    quantity_required: Decimal = Field(..., description="Quantity required")
    unit_of_measure: str = Field(..., min_length=1, max_length=50, description="Unit of measure")
    parent_bom_id: Optional[int] = Field(None, description="Parent BOM ID for hierarchy")
    level: int = Field(default=1, ge=1, description="BOM level")
    sequence: int = Field(default=0, ge=0, description="Sequence order")
    reference_designator: Optional[str] = Field(None, max_length=100, description="Reference designator")
    drawing_reference: Optional[str] = Field(None, max_length=100, description="Drawing reference")
    find_number: Optional[str] = Field(None, max_length=50, description="Find number")
    supplier: Optional[str] = Field(None, max_length=200, description="Supplier")
    lead_time_days: Optional[int] = Field(None, description="Lead time in days")
    unit_cost: Optional[Decimal] = Field(None, description="Unit cost")
    notes: Optional[str] = Field(None, description="Notes")
    special_instructions: Optional[str] = Field(None, description="Special instructions")
    is_critical: bool = Field(default=False, description="Is critical item")
    is_optional: bool = Field(default=False, description="Is optional item")

    @field_validator('bom_type')
    @classmethod
    def validate_bom_type(cls, v):
        """Validate BOM type"""
        valid_types = ['PROJECT_BOM', 'ASSEMBLY_BOM', 'PROCUREMENT_BOM']
        if v not in valid_types:
            raise ValueError(f'bom_type must be one of {valid_types}')
        return v


class ProjectBOMUpdateDTO(BaseModel):
    """DTO for updating a project BOM item"""
    description: Optional[str] = None
    part_number: Optional[str] = Field(None, max_length=100)
    part_description: Optional[str] = Field(None, max_length=500)
    quantity_required: Optional[Decimal] = None
    quantity_allocated: Optional[Decimal] = None
    quantity_issued: Optional[Decimal] = None
    reference_designator: Optional[str] = Field(None, max_length=100)
    drawing_reference: Optional[str] = Field(None, max_length=100)
    find_number: Optional[str] = Field(None, max_length=50)
    procurement_status: Optional[str] = None
    supplier: Optional[str] = Field(None, max_length=200)
    lead_time_days: Optional[int] = None
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    is_critical: Optional[bool] = None
    is_optional: Optional[bool] = None
    is_active: Optional[bool] = None


class ProjectBOMResponse(BaseModel):
    """DTO for project BOM response"""
    id: int
    organization_id: int
    project_id: int
    bom_code: str
    description: Optional[str]
    bom_type: str
    material_id: Optional[int]
    part_number: Optional[str]
    part_description: Optional[str]
    quantity_required: Decimal
    unit_of_measure: str
    quantity_allocated: Decimal
    quantity_issued: Decimal
    parent_bom_id: Optional[int]
    level: int
    sequence: int
    reference_designator: Optional[str]
    drawing_reference: Optional[str]
    find_number: Optional[str]
    procurement_status: Optional[str]
    supplier: Optional[str]
    lead_time_days: Optional[int]
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    notes: Optional[str]
    special_instructions: Optional[str]
    is_critical: bool
    is_optional: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ========== Helper DTOs ==========

class DocumentVersionCreateDTO(BaseModel):
    """DTO for creating a new version of a document"""
    version: str = Field(..., min_length=1, max_length=50, description="New version number")
    file_path: str = Field(..., min_length=1, max_length=500, description="New file path")
    file_name: str = Field(..., min_length=1, max_length=255, description="New file name")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    checksum: Optional[str] = Field(None, max_length=64, description="SHA-256 checksum")
    description: Optional[str] = Field(None, description="Version description/notes")


class MilestoneProgressUpdateDTO(BaseModel):
    """DTO for updating milestone progress"""
    completion_percentage: int = Field(..., ge=0, le=100, description="Completion percentage")
    status: Optional[str] = Field(None, description="Status")
    notes: Optional[str] = Field(None, description="Progress notes")
