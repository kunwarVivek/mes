"""
Project Management Service - Business logic for documents, milestones, RDA, BOM
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.project_management import ProjectDocument, ProjectMilestone, RDADrawing, ProjectBOM
from app.infrastructure.repositories.project_management_repository import (
    ProjectDocumentRepository,
    ProjectMilestoneRepository,
    RDADrawingRepository,
    ProjectBOMRepository,
)
from app.application.dtos.project_management_dto import (
    ProjectDocumentCreateDTO,
    ProjectDocumentUpdateDTO,
    ProjectMilestoneCreateDTO,
    ProjectMilestoneUpdateDTO,
    RDADrawingCreateDTO,
    RDADrawingUpdateDTO,
    RDADrawingSubmitDTO,
    RDADrawingReviewDTO,
    ProjectBOMCreateDTO,
    ProjectBOMUpdateDTO,
    DocumentVersionCreateDTO,
    MilestoneProgressUpdateDTO,
)


class ProjectDocumentService:
    """Service for Project Document operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ProjectDocumentRepository(db)

    def create_document(self, dto: ProjectDocumentCreateDTO, uploaded_by: int) -> ProjectDocument:
        """Create a new project document"""
        # Check for duplicate document code in project
        existing_versions = self.repo.get_document_versions(dto.document_code, dto.project_id)
        if existing_versions:
            # This is a new version of existing document
            latest_version = existing_versions[0]
            # Auto-increment revision
            dto.revision = latest_version.revision + 1

        return self.repo.create(dto, uploaded_by)

    def create_document_version(self, document_id: int, dto: DocumentVersionCreateDTO,
                               uploaded_by: int) -> ProjectDocument:
        """Create a new version of an existing document"""
        original = self.repo.get_by_id(document_id)
        if not original:
            raise ValueError(f"Document with ID {document_id} not found")

        # Create new version DTO based on original
        new_version_dto = ProjectDocumentCreateDTO(
            project_id=original.project_id,
            organization_id=original.organization_id,
            document_name=original.document_name,
            document_code=original.document_code,
            description=dto.description or original.description,
            document_type=original.document_type,
            category=original.category,
            version=dto.version,
            file_path=dto.file_path,
            file_name=dto.file_name,
            file_size_bytes=dto.file_size_bytes,
            mime_type=original.mime_type,
            checksum=dto.checksum,
            tags=original.tags,
            metadata=original.metadata,
            is_public=original.is_public,
            requires_approval=original.requires_approval,
            parent_document_id=document_id,  # Link to original
        )

        return self.repo.create(new_version_dto, uploaded_by)

    def get_document(self, document_id: int) -> Optional[ProjectDocument]:
        """Get document by ID"""
        return self.repo.get_by_id(document_id)

    def list_documents(self, project_id: int, skip: int = 0, limit: int = 100,
                      latest_only: bool = True, document_type: Optional[str] = None) -> List[ProjectDocument]:
        """List documents for a project"""
        return self.repo.list_by_project(project_id, skip, limit, latest_only, document_type)

    def get_document_versions(self, document_code: str, project_id: int) -> List[ProjectDocument]:
        """Get all versions of a document"""
        return self.repo.get_document_versions(document_code, project_id)

    def update_document(self, document_id: int, dto: ProjectDocumentUpdateDTO) -> Optional[ProjectDocument]:
        """Update document"""
        return self.repo.update(document_id, dto)

    def delete_document(self, document_id: int) -> bool:
        """Delete document (soft delete)"""
        return self.repo.delete(document_id)

    def archive_document(self, document_id: int) -> Optional[ProjectDocument]:
        """Archive a document"""
        dto = ProjectDocumentUpdateDTO(is_archived=True)
        return self.repo.update(document_id, dto)


class ProjectMilestoneService:
    """Service for Project Milestone operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ProjectMilestoneRepository(db)

    def create_milestone(self, dto: ProjectMilestoneCreateDTO) -> ProjectMilestone:
        """Create a new project milestone"""
        return self.repo.create(dto)

    def get_milestone(self, milestone_id: int) -> Optional[ProjectMilestone]:
        """Get milestone by ID"""
        return self.repo.get_by_id(milestone_id)

    def list_milestones(self, project_id: int, skip: int = 0, limit: int = 100,
                       status: Optional[str] = None, critical_only: bool = False) -> List[ProjectMilestone]:
        """List milestones for a project"""
        return self.repo.list_by_project(project_id, skip, limit, status, critical_only)

    def update_milestone(self, milestone_id: int, dto: ProjectMilestoneUpdateDTO) -> Optional[ProjectMilestone]:
        """Update milestone"""
        return self.repo.update(milestone_id, dto)

    def update_progress(self, milestone_id: int, dto: MilestoneProgressUpdateDTO) -> Optional[ProjectMilestone]:
        """Update milestone progress"""
        update_dto = ProjectMilestoneUpdateDTO(
            completion_percentage=dto.completion_percentage,
            status=dto.status,
            notes=dto.notes,
        )

        # Auto-complete if 100%
        if dto.completion_percentage == 100 and not dto.status:
            update_dto.status = 'COMPLETED'

        return self.repo.update(milestone_id, update_dto)

    def complete_milestone(self, milestone_id: int, notes: Optional[str] = None) -> Optional[ProjectMilestone]:
        """Mark milestone as completed"""
        dto = ProjectMilestoneUpdateDTO(
            status='COMPLETED',
            completion_percentage=100,
            actual_date=datetime.now(timezone.utc).date(),
            notes=notes,
        )
        return self.repo.update(milestone_id, dto)

    def delete_milestone(self, milestone_id: int) -> bool:
        """Delete milestone (soft delete)"""
        return self.repo.delete(milestone_id)

    def get_overdue_milestones(self, project_id: int) -> List[ProjectMilestone]:
        """Get overdue milestones for a project"""
        all_milestones = self.repo.list_by_project(project_id, limit=1000)
        return [m for m in all_milestones if m.is_overdue()]

    def get_critical_path(self, project_id: int) -> List[ProjectMilestone]:
        """Get critical path milestones"""
        return self.repo.list_by_project(project_id, limit=1000, critical_only=True)


class RDADrawingService:
    """Service for RDA (Request for Drawing Approval) operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = RDADrawingRepository(db)

    def create_rda(self, dto: RDADrawingCreateDTO, submitted_by: int) -> RDADrawing:
        """Create a new RDA"""
        return self.repo.create(dto, submitted_by)

    def get_rda(self, rda_id: int) -> Optional[RDADrawing]:
        """Get RDA by ID"""
        return self.repo.get_by_id(rda_id)

    def list_rdas(self, project_id: int, skip: int = 0, limit: int = 100,
                 approval_status: Optional[str] = None) -> List[RDADrawing]:
        """List RDAs for a project"""
        return self.repo.list_by_project(project_id, skip, limit, approval_status)

    def update_rda(self, rda_id: int, dto: RDADrawingUpdateDTO) -> Optional[RDADrawing]:
        """Update RDA"""
        rda = self.repo.get_by_id(rda_id)
        if not rda:
            return None

        # Can only update if in DRAFT status
        if rda.approval_status != 'DRAFT':
            raise ValueError("Can only update RDA in DRAFT status")

        return self.repo.update(rda_id, dto)

    def submit_for_approval(self, rda_id: int, dto: RDADrawingSubmitDTO) -> Optional[RDADrawing]:
        """Submit RDA for approval"""
        rda = self.repo.get_by_id(rda_id)
        if not rda:
            return None

        if rda.approval_status != 'DRAFT':
            raise ValueError("Can only submit RDA in DRAFT status")

        # Initialize approvers with pending status
        approvers = [
            {
                "user_id": approver["user_id"],
                "role": approver["role"],
                "status": "pending",
                "date": None,
                "comments": None
            }
            for approver in dto.approvers
        ]

        return self.repo.submit_for_approval(rda_id, approvers)

    def review_rda(self, rda_id: int, dto: RDADrawingReviewDTO, user_id: int) -> Optional[RDADrawing]:
        """Review an RDA (approve or reject)"""
        rda = self.repo.get_by_id(rda_id)
        if not rda:
            return None

        if rda.approval_status not in ['SUBMITTED', 'IN_REVIEW']:
            raise ValueError("Can only review RDA in SUBMITTED or IN_REVIEW status")

        # Check if user is an approver
        if rda.approvers:
            user_is_approver = any(a.get("user_id") == user_id for a in rda.approvers)
            if not user_is_approver:
                raise PermissionError("User is not an approver for this RDA")

            # Update approver status
            for approver in rda.approvers:
                if approver.get("user_id") == user_id:
                    approver["status"] = dto.status.lower()
                    approver["date"] = datetime.now(timezone.utc).isoformat()
                    approver["comments"] = dto.comments

            # Check if all approvers have responded
            all_responded = all(a.get("status") != "pending" for a in rda.approvers)
            all_approved = all(a.get("status") == "approved" for a in rda.approvers)

            if all_responded:
                if all_approved:
                    final_status = 'APPROVED'
                else:
                    final_status = 'REJECTED'
            else:
                final_status = 'IN_REVIEW'
        else:
            # No approvers defined, use simple approval
            final_status = dto.status

        return self.repo.update_approval_status(rda_id, final_status, user_id, dto.comments)

    def get_pending_approvals(self, project_id: int, user_id: int) -> List[RDADrawing]:
        """Get RDAs pending approval by a specific user"""
        rdas = self.repo.list_by_project(project_id, limit=1000,
                                        approval_status='SUBMITTED')
        rdas.extend(self.repo.list_by_project(project_id, limit=1000,
                                             approval_status='IN_REVIEW'))

        # Filter for user's pending approvals
        pending = []
        for rda in rdas:
            if rda.approvers:
                for approver in rda.approvers:
                    if approver.get("user_id") == user_id and approver.get("status") == "pending":
                        pending.append(rda)
                        break

        return pending


class ProjectBOMService:
    """Service for Project BOM operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ProjectBOMRepository(db)

    def create_bom_item(self, dto: ProjectBOMCreateDTO) -> ProjectBOM:
        """Create a new project BOM item"""
        return self.repo.create(dto)

    def get_bom_item(self, bom_id: int) -> Optional[ProjectBOM]:
        """Get BOM item by ID"""
        return self.repo.get_by_id(bom_id)

    def list_bom_items(self, project_id: int, skip: int = 0, limit: int = 1000,
                      parent_id: Optional[int] = None, level: Optional[int] = None) -> List[ProjectBOM]:
        """List BOM items for a project"""
        return self.repo.list_by_project(project_id, skip, limit, parent_id, level)

    def get_bom_tree(self, project_id: int) -> List[ProjectBOM]:
        """Get hierarchical BOM tree"""
        return self.repo.get_bom_tree(project_id)

    def update_bom_item(self, bom_id: int, dto: ProjectBOMUpdateDTO) -> Optional[ProjectBOM]:
        """Update BOM item"""
        return self.repo.update(bom_id, dto)

    def allocate_quantity(self, bom_id: int, quantity: float) -> Optional[ProjectBOM]:
        """Allocate quantity to BOM item"""
        bom = self.repo.get_by_id(bom_id)
        if not bom:
            return None

        new_allocated = float(bom.quantity_allocated) + quantity
        if new_allocated > float(bom.quantity_required):
            raise ValueError(f"Cannot allocate {quantity}. Would exceed required quantity.")

        dto = ProjectBOMUpdateDTO(quantity_allocated=new_allocated)
        return self.repo.update(bom_id, dto)

    def issue_quantity(self, bom_id: int, quantity: float) -> Optional[ProjectBOM]:
        """Issue quantity from BOM item"""
        bom = self.repo.get_by_id(bom_id)
        if not bom:
            return None

        new_issued = float(bom.quantity_issued) + quantity
        if new_issued > float(bom.quantity_allocated):
            raise ValueError(f"Cannot issue {quantity}. Would exceed allocated quantity.")

        dto = ProjectBOMUpdateDTO(
            quantity_issued=new_issued,
            procurement_status='ISSUED' if new_issued >= float(bom.quantity_required) else 'PARTIALLY_ISSUED'
        )
        return self.repo.update(bom_id, dto)

    def delete_bom_item(self, bom_id: int) -> bool:
        """Delete BOM item (soft delete)"""
        return self.repo.delete(bom_id)

    def get_critical_items(self, project_id: int) -> List[ProjectBOM]:
        """Get critical BOM items"""
        all_items = self.repo.list_by_project(project_id, limit=10000)
        return [item for item in all_items if item.is_critical]

    def get_procurement_summary(self, project_id: int) -> dict:
        """Get procurement summary for project BOM"""
        all_items = self.repo.list_by_project(project_id, limit=10000)

        total_items = len(all_items)
        fully_allocated = sum(1 for item in all_items if item.is_fully_allocated())
        fully_issued = sum(1 for item in all_items if item.is_fully_issued())

        total_cost = sum(float(item.total_cost or 0) for item in all_items)

        return {
            "total_items": total_items,
            "fully_allocated": fully_allocated,
            "fully_issued": fully_issued,
            "allocation_percentage": (fully_allocated / total_items * 100) if total_items > 0 else 0,
            "issue_percentage": (fully_issued / total_items * 100) if total_items > 0 else 0,
            "total_cost": total_cost,
        }
