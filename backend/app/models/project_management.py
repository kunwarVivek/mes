"""
Project Management models - Documents, Milestones, RDA, BOM
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, Numeric, Index, UniqueConstraint, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum
from typing import Optional
from datetime import datetime, timezone, date


# Enums
class DocumentType(str, Enum):
    """Document type enumeration"""
    DRAWING = "DRAWING"
    SPEC = "SPEC"
    REPORT = "REPORT"
    CONTRACT = "CONTRACT"
    PROCEDURE = "PROCEDURE"
    MANUAL = "MANUAL"
    OTHER = "OTHER"


class MilestoneStatus(str, Enum):
    """Milestone status enumeration"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class RDAApprovalStatus(str, Enum):
    """RDA approval status enumeration"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class RDAPriority(str, Enum):
    """RDA priority enumeration"""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class BOMType(str, Enum):
    """BOM type enumeration"""
    PROJECT_BOM = "PROJECT_BOM"
    ASSEMBLY_BOM = "ASSEMBLY_BOM"
    PROCUREMENT_BOM = "PROCUREMENT_BOM"


class ProjectDocument(Base):
    """
    Project document model with version control.

    Supports:
    - Document versioning and revision history
    - Multiple document types (drawings, specs, reports, etc.)
    - File storage with checksums
    - Approval workflows
    - Archiving and access control
    """
    __tablename__ = 'project_documents'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)

    # Document identification
    document_name = Column(String(200), nullable=False)
    document_code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)

    # Version control
    version = Column(String(50), nullable=False)
    revision = Column(Integer, nullable=False, default=1)
    is_latest_version = Column(Boolean, nullable=False, default=True)
    parent_document_id = Column(Integer, ForeignKey('project_documents.id', ondelete='SET NULL'), nullable=True)

    # File information
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA-256

    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Ownership and access
    uploaded_by = Column(Integer, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False)
    requires_approval = Column(Boolean, nullable=False, default=False)
    approval_status = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_archived = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="documents", foreign_keys=[project_id])
    previous_versions = relationship("ProjectDocument",
                                    remote_side=[parent_document_id],
                                    backref="newer_version")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'document_code', 'version', name='uq_project_document_version'),
        Index('idx_project_documents_org', 'organization_id'),
        Index('idx_project_documents_project', 'project_id'),
        Index('idx_project_documents_type', 'document_type'),
        Index('idx_project_documents_latest', 'project_id', 'is_latest_version'),
        CheckConstraint(
            "document_type IN ('DRAWING', 'SPEC', 'REPORT', 'CONTRACT', 'PROCEDURE', 'MANUAL', 'OTHER')",
            name='chk_document_type_valid'
        ),
    )

    def __repr__(self):
        return f"<ProjectDocument(id={self.id}, code='{self.document_code}', version='{self.version}')>"

    def get_file_size_display(self) -> str:
        """Get human-readable file size"""
        if not self.file_size_bytes:
            return "Unknown"

        size = self.file_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"


class ProjectMilestone(Base):
    """
    Project milestone model for tracking key deliverables and dates.

    Supports:
    - Critical path tracking
    - Dependency management
    - Progress monitoring
    - Deliverable tracking
    - Alert notifications
    """
    __tablename__ = 'project_milestones'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)

    # Milestone identification
    milestone_name = Column(String(200), nullable=False)
    milestone_code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    milestone_type = Column(String(50), nullable=False)

    # Scheduling
    planned_date = Column(Date, nullable=False)
    baseline_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    is_critical_path = Column(Boolean, nullable=False, default=False)

    # Progress tracking
    status = Column(String(50), nullable=False)
    completion_percentage = Column(Integer, nullable=False, default=0)
    dependencies = Column(ARRAY(Integer), nullable=True)

    # Deliverables
    deliverables = Column(JSONB, nullable=True)

    # Responsibility
    owner_user_id = Column(Integer, nullable=True)
    assigned_team = Column(String(100), nullable=True)

    # Notifications
    alert_days_before = Column(Integer, nullable=True)
    alert_recipients = Column(ARRAY(String), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="milestones", foreign_keys=[project_id])

    # Table constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'milestone_code', name='uq_project_milestone_code'),
        Index('idx_project_milestones_org', 'organization_id'),
        Index('idx_project_milestones_project', 'project_id'),
        Index('idx_project_milestones_status', 'status'),
        Index('idx_project_milestones_date', 'planned_date'),
        CheckConstraint(
            "status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'DELAYED', 'CANCELLED')",
            name='chk_milestone_status_valid'
        ),
        CheckConstraint(
            "completion_percentage >= 0 AND completion_percentage <= 100",
            name='chk_milestone_completion_valid'
        ),
    )

    def __repr__(self):
        return f"<ProjectMilestone(id={self.id}, code='{self.milestone_code}', status='{self.status}')>"

    def is_overdue(self) -> bool:
        """Check if milestone is overdue"""
        if self.status == MilestoneStatus.COMPLETED.value:
            return False
        if not self.planned_date:
            return False
        return date.today() > self.planned_date

    def days_until_due(self) -> Optional[int]:
        """Calculate days until milestone is due (negative if overdue)"""
        if not self.planned_date:
            return None
        delta = self.planned_date - date.today()
        return delta.days


class RDADrawing(Base):
    """
    Request for Drawing Approval (RDA) model.

    Integrates with workflow engine for approval routing.
    Tracks drawing submissions, reviews, and approvals.
    """
    __tablename__ = 'rda_drawings'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey('project_documents.id', ondelete='SET NULL'), nullable=True)

    # RDA identification
    rda_number = Column(String(100), nullable=False)
    drawing_number = Column(String(100), nullable=False)
    drawing_title = Column(String(200), nullable=False)
    revision = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    # Workflow integration
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='SET NULL'), nullable=True)
    current_workflow_state_id = Column(Integer, nullable=True)
    approval_status = Column(String(50), nullable=False)

    # Submission details
    submitted_by = Column(Integer, nullable=False)
    submitted_date = Column(DateTime(timezone=True), nullable=True)
    required_approval_date = Column(Date, nullable=True)
    priority = Column(String(50), nullable=False, default='NORMAL')

    # Approval tracking
    approvers = Column(JSONB, nullable=True)
    review_comments = Column(ARRAY(JSONB), nullable=True)

    # Approval decision
    approved_date = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    rejection_date = Column(DateTime(timezone=True), nullable=True)

    # Distribution
    distribution_list = Column(ARRAY(String), nullable=True)
    notify_on_approval = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="rda_drawings", foreign_keys=[project_id])
    document = relationship("ProjectDocument", foreign_keys=[document_id])

    # Table constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'rda_number', name='uq_project_rda_number'),
        Index('idx_rda_drawings_org', 'organization_id'),
        Index('idx_rda_drawings_project', 'project_id'),
        Index('idx_rda_drawings_status', 'approval_status'),
        Index('idx_rda_drawings_drawing_number', 'drawing_number'),
        CheckConstraint(
            "approval_status IN ('DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'SUPERSEDED')",
            name='chk_rda_status_valid'
        ),
        CheckConstraint(
            "priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')",
            name='chk_rda_priority_valid'
        ),
    )

    def __repr__(self):
        return f"<RDADrawing(id={self.id}, rda_number='{self.rda_number}', status='{self.approval_status}')>"

    def is_pending_approval(self) -> bool:
        """Check if RDA is pending approval"""
        return self.approval_status in [RDAApprovalStatus.SUBMITTED.value, RDAApprovalStatus.IN_REVIEW.value]

    def is_approved(self) -> bool:
        """Check if RDA is approved"""
        return self.approval_status == RDAApprovalStatus.APPROVED.value


class ProjectBOM(Base):
    """
    Project Bill of Materials model.

    Supports:
    - Hierarchical BOM structure
    - Material tracking and allocation
    - Procurement status
    - Cost tracking
    """
    __tablename__ = 'project_bom'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)

    # BOM identification
    bom_code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    bom_type = Column(String(50), nullable=False)

    # Item details
    material_id = Column(Integer, ForeignKey('materials.id', ondelete='SET NULL'), nullable=True)
    part_number = Column(String(100), nullable=True)
    part_description = Column(String(500), nullable=True)

    # Quantity and units
    quantity_required = Column(Numeric(precision=15, scale=4), nullable=False)
    unit_of_measure = Column(String(50), nullable=False)
    quantity_allocated = Column(Numeric(precision=15, scale=4), nullable=False, default=0)
    quantity_issued = Column(Numeric(precision=15, scale=4), nullable=False, default=0)

    # Hierarchy
    parent_bom_id = Column(Integer, ForeignKey('project_bom.id', ondelete='CASCADE'), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    sequence = Column(Integer, nullable=False, default=0)

    # References
    reference_designator = Column(String(100), nullable=True)
    drawing_reference = Column(String(100), nullable=True)
    find_number = Column(String(50), nullable=True)

    # Procurement
    procurement_status = Column(String(50), nullable=True)
    supplier = Column(String(200), nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    unit_cost = Column(Numeric(precision=15, scale=2), nullable=True)
    total_cost = Column(Numeric(precision=15, scale=2), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)

    # Status
    is_critical = Column(Boolean, nullable=False, default=False)
    is_optional = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="bom_items", foreign_keys=[project_id])
    material = relationship("Material", foreign_keys=[material_id])
    parent_bom = relationship("ProjectBOM", remote_side=[id], backref="children")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'bom_code', name='uq_project_bom_code'),
        Index('idx_project_bom_org', 'organization_id'),
        Index('idx_project_bom_project', 'project_id'),
        Index('idx_project_bom_material', 'material_id'),
        Index('idx_project_bom_parent', 'parent_bom_id'),
        Index('idx_project_bom_level', 'project_id', 'level'),
        CheckConstraint(
            "bom_type IN ('PROJECT_BOM', 'ASSEMBLY_BOM', 'PROCUREMENT_BOM')",
            name='chk_project_bom_type_valid'
        ),
    )

    def __repr__(self):
        return f"<ProjectBOM(id={self.id}, code='{self.bom_code}', type='{self.bom_type}')>"

    def get_quantity_remaining(self) -> float:
        """Calculate remaining quantity to be allocated"""
        return float(self.quantity_required - self.quantity_allocated)

    def get_quantity_unissued(self) -> float:
        """Calculate allocated but not issued quantity"""
        return float(self.quantity_allocated - self.quantity_issued)

    def is_fully_allocated(self) -> bool:
        """Check if BOM item is fully allocated"""
        return self.quantity_allocated >= self.quantity_required

    def is_fully_issued(self) -> bool:
        """Check if BOM item is fully issued"""
        return self.quantity_issued >= self.quantity_required
