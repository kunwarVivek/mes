"""
Repository for Project Management (Documents, Milestones, RDA, BOM)
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from datetime import datetime, timezone

from app.models.project_management import (
    ProjectDocument,
    ProjectMilestone,
    RDADrawing,
    ProjectBOM
)
from app.application.dtos.project_management_dto import (
    ProjectDocumentCreateDTO,
    ProjectDocumentUpdateDTO,
    ProjectMilestoneCreateDTO,
    ProjectMilestoneUpdateDTO,
    RDADrawingCreateDTO,
    RDADrawingUpdateDTO,
    ProjectBOMCreateDTO,
    ProjectBOMUpdateDTO,
)


class ProjectDocumentRepository:
    """Repository for ProjectDocument operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: ProjectDocumentCreateDTO, uploaded_by: int) -> ProjectDocument:
        """Create a new project document"""
        # Mark other versions as not latest if this is the latest
        if not dto.parent_document_id:
            # This is a new document, mark it as latest
            is_latest = True
        else:
            # This is a new version, mark parent as not latest
            parent = self.get_by_id(dto.parent_document_id)
            if parent:
                parent.is_latest_version = False
            is_latest = True

        document = ProjectDocument(
            organization_id=dto.organization_id,
            project_id=dto.project_id,
            document_name=dto.document_name,
            document_code=dto.document_code,
            description=dto.description,
            document_type=dto.document_type,
            category=dto.category,
            version=dto.version,
            file_path=dto.file_path,
            file_name=dto.file_name,
            file_size_bytes=dto.file_size_bytes,
            mime_type=dto.mime_type,
            checksum=dto.checksum,
            tags=dto.tags,
            metadata=dto.metadata,
            uploaded_by=uploaded_by,
            is_public=dto.is_public,
            requires_approval=dto.requires_approval,
            is_latest_version=is_latest,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_by_id(self, document_id: int) -> Optional[ProjectDocument]:
        """Get document by ID"""
        return self.db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

    def list_by_project(self, project_id: int, skip: int = 0, limit: int = 100,
                       latest_only: bool = True, document_type: Optional[str] = None) -> List[ProjectDocument]:
        """List documents for a project"""
        query = self.db.query(ProjectDocument).filter(
            and_(
                ProjectDocument.project_id == project_id,
                ProjectDocument.is_active == True
            )
        )

        if latest_only:
            query = query.filter(ProjectDocument.is_latest_version == True)

        if document_type:
            query = query.filter(ProjectDocument.document_type == document_type)

        return query.order_by(desc(ProjectDocument.created_at)).offset(skip).limit(limit).all()

    def get_document_versions(self, document_code: str, project_id: int) -> List[ProjectDocument]:
        """Get all versions of a document"""
        return self.db.query(ProjectDocument).filter(
            and_(
                ProjectDocument.project_id == project_id,
                ProjectDocument.document_code == document_code
            )
        ).order_by(desc(ProjectDocument.revision)).all()

    def update(self, document_id: int, dto: ProjectDocumentUpdateDTO) -> Optional[ProjectDocument]:
        """Update document"""
        document = self.get_by_id(document_id)
        if not document:
            return None

        if dto.document_name:
            document.document_name = dto.document_name
        if dto.description is not None:
            document.description = dto.description
        if dto.category is not None:
            document.category = dto.category
        if dto.tags is not None:
            document.tags = dto.tags
        if dto.metadata is not None:
            document.metadata = dto.metadata
        if dto.is_public is not None:
            document.is_public = dto.is_public
        if dto.approval_status is not None:
            document.approval_status = dto.approval_status
        if dto.is_archived is not None:
            document.is_archived = dto.is_archived
            if dto.is_archived:
                document.archived_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document_id: int) -> bool:
        """Delete document (soft delete)"""
        document = self.get_by_id(document_id)
        if not document:
            return False

        document.is_active = False
        self.db.commit()
        return True


class ProjectMilestoneRepository:
    """Repository for ProjectMilestone operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: ProjectMilestoneCreateDTO) -> ProjectMilestone:
        """Create a new project milestone"""
        milestone = ProjectMilestone(
            organization_id=dto.organization_id,
            project_id=dto.project_id,
            milestone_name=dto.milestone_name,
            milestone_code=dto.milestone_code,
            description=dto.description,
            milestone_type=dto.milestone_type,
            planned_date=dto.planned_date,
            baseline_date=dto.baseline_date or dto.planned_date,
            is_critical_path=dto.is_critical_path,
            status='NOT_STARTED',
            dependencies=dto.dependencies,
            deliverables=dto.deliverables,
            owner_user_id=dto.owner_user_id,
            assigned_team=dto.assigned_team,
            alert_days_before=dto.alert_days_before,
            alert_recipients=dto.alert_recipients,
            notes=dto.notes,
            display_order=dto.display_order,
        )
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def get_by_id(self, milestone_id: int) -> Optional[ProjectMilestone]:
        """Get milestone by ID"""
        return self.db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()

    def list_by_project(self, project_id: int, skip: int = 0, limit: int = 100,
                       status: Optional[str] = None, critical_only: bool = False) -> List[ProjectMilestone]:
        """List milestones for a project"""
        query = self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.project_id == project_id,
                ProjectMilestone.is_active == True
            )
        )

        if status:
            query = query.filter(ProjectMilestone.status == status)

        if critical_only:
            query = query.filter(ProjectMilestone.is_critical_path == True)

        return query.order_by(ProjectMilestone.display_order, ProjectMilestone.planned_date).offset(skip).limit(limit).all()

    def update(self, milestone_id: int, dto: ProjectMilestoneUpdateDTO) -> Optional[ProjectMilestone]:
        """Update milestone"""
        milestone = self.get_by_id(milestone_id)
        if not milestone:
            return None

        if dto.milestone_name:
            milestone.milestone_name = dto.milestone_name
        if dto.description is not None:
            milestone.description = dto.description
        if dto.planned_date is not None:
            milestone.planned_date = dto.planned_date
        if dto.baseline_date is not None:
            milestone.baseline_date = dto.baseline_date
        if dto.actual_date is not None:
            milestone.actual_date = dto.actual_date
        if dto.is_critical_path is not None:
            milestone.is_critical_path = dto.is_critical_path
        if dto.status is not None:
            milestone.status = dto.status
            if dto.status == 'COMPLETED' and not milestone.completed_at:
                milestone.completed_at = datetime.now(timezone.utc)
                milestone.completion_percentage = 100
        if dto.completion_percentage is not None:
            milestone.completion_percentage = dto.completion_percentage
        if dto.dependencies is not None:
            milestone.dependencies = dto.dependencies
        if dto.deliverables is not None:
            milestone.deliverables = dto.deliverables
        if dto.owner_user_id is not None:
            milestone.owner_user_id = dto.owner_user_id
        if dto.assigned_team is not None:
            milestone.assigned_team = dto.assigned_team
        if dto.alert_days_before is not None:
            milestone.alert_days_before = dto.alert_days_before
        if dto.alert_recipients is not None:
            milestone.alert_recipients = dto.alert_recipients
        if dto.notes is not None:
            milestone.notes = dto.notes
        if dto.display_order is not None:
            milestone.display_order = dto.display_order
        if dto.is_active is not None:
            milestone.is_active = dto.is_active

        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def delete(self, milestone_id: int) -> bool:
        """Delete milestone (soft delete)"""
        milestone = self.get_by_id(milestone_id)
        if not milestone:
            return False

        milestone.is_active = False
        self.db.commit()
        return True


class RDADrawingRepository:
    """Repository for RDADrawing operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: RDADrawingCreateDTO, submitted_by: int) -> RDADrawing:
        """Create a new RDA drawing"""
        rda = RDADrawing(
            organization_id=dto.organization_id,
            project_id=dto.project_id,
            document_id=dto.document_id,
            rda_number=dto.rda_number,
            drawing_number=dto.drawing_number,
            drawing_title=dto.drawing_title,
            revision=dto.revision,
            description=dto.description,
            workflow_id=dto.workflow_id,
            approval_status='DRAFT',
            submitted_by=submitted_by,
            required_approval_date=dto.required_approval_date,
            priority=dto.priority,
            distribution_list=dto.distribution_list,
            notify_on_approval=dto.notify_on_approval,
        )
        self.db.add(rda)
        self.db.commit()
        self.db.refresh(rda)
        return rda

    def get_by_id(self, rda_id: int) -> Optional[RDADrawing]:
        """Get RDA by ID"""
        return self.db.query(RDADrawing).filter(RDADrawing.id == rda_id).first()

    def list_by_project(self, project_id: int, skip: int = 0, limit: int = 100,
                       approval_status: Optional[str] = None) -> List[RDADrawing]:
        """List RDA drawings for a project"""
        query = self.db.query(RDADrawing).filter(RDADrawing.project_id == project_id)

        if approval_status:
            query = query.filter(RDADrawing.approval_status == approval_status)

        return query.order_by(desc(RDADrawing.created_at)).offset(skip).limit(limit).all()

    def update(self, rda_id: int, dto: RDADrawingUpdateDTO) -> Optional[RDADrawing]:
        """Update RDA drawing"""
        rda = self.get_by_id(rda_id)
        if not rda:
            return None

        if dto.drawing_title:
            rda.drawing_title = dto.drawing_title
        if dto.description is not None:
            rda.description = dto.description
        if dto.required_approval_date is not None:
            rda.required_approval_date = dto.required_approval_date
        if dto.priority is not None:
            rda.priority = dto.priority
        if dto.distribution_list is not None:
            rda.distribution_list = dto.distribution_list
        if dto.notify_on_approval is not None:
            rda.notify_on_approval = dto.notify_on_approval

        self.db.commit()
        self.db.refresh(rda)
        return rda

    def submit_for_approval(self, rda_id: int, approvers: List[dict]) -> Optional[RDADrawing]:
        """Submit RDA for approval"""
        rda = self.get_by_id(rda_id)
        if not rda:
            return None

        rda.approval_status = 'SUBMITTED'
        rda.submitted_date = datetime.now(timezone.utc)
        rda.approvers = approvers

        self.db.commit()
        self.db.refresh(rda)
        return rda

    def update_approval_status(self, rda_id: int, status: str, user_id: int,
                              comments: Optional[str] = None) -> Optional[RDADrawing]:
        """Update approval status"""
        rda = self.get_by_id(rda_id)
        if not rda:
            return None

        rda.approval_status = status

        if status == 'APPROVED':
            rda.approved_date = datetime.now(timezone.utc)
            rda.approved_by = user_id
        elif status == 'REJECTED':
            rda.rejection_date = datetime.now(timezone.utc)
            rda.rejection_reason = comments

        # Add review comment
        if comments:
            comment = {
                "user_id": user_id,
                "comment": comments,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "general"
            }
            if rda.review_comments:
                rda.review_comments.append(comment)
            else:
                rda.review_comments = [comment]

        self.db.commit()
        self.db.refresh(rda)
        return rda


class ProjectBOMRepository:
    """Repository for ProjectBOM operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: ProjectBOMCreateDTO) -> ProjectBOM:
        """Create a new project BOM item"""
        # Calculate total cost if unit cost provided
        total_cost = None
        if dto.unit_cost:
            total_cost = dto.unit_cost * dto.quantity_required

        bom = ProjectBOM(
            organization_id=dto.organization_id,
            project_id=dto.project_id,
            bom_code=dto.bom_code,
            description=dto.description,
            bom_type=dto.bom_type,
            material_id=dto.material_id,
            part_number=dto.part_number,
            part_description=dto.part_description,
            quantity_required=dto.quantity_required,
            unit_of_measure=dto.unit_of_measure,
            parent_bom_id=dto.parent_bom_id,
            level=dto.level,
            sequence=dto.sequence,
            reference_designator=dto.reference_designator,
            drawing_reference=dto.drawing_reference,
            find_number=dto.find_number,
            supplier=dto.supplier,
            lead_time_days=dto.lead_time_days,
            unit_cost=dto.unit_cost,
            total_cost=total_cost,
            notes=dto.notes,
            special_instructions=dto.special_instructions,
            is_critical=dto.is_critical,
            is_optional=dto.is_optional,
        )
        self.db.add(bom)
        self.db.commit()
        self.db.refresh(bom)
        return bom

    def get_by_id(self, bom_id: int) -> Optional[ProjectBOM]:
        """Get BOM item by ID"""
        return self.db.query(ProjectBOM).filter(ProjectBOM.id == bom_id).first()

    def list_by_project(self, project_id: int, skip: int = 0, limit: int = 1000,
                       parent_id: Optional[int] = None, level: Optional[int] = None) -> List[ProjectBOM]:
        """List BOM items for a project"""
        query = self.db.query(ProjectBOM).filter(
            and_(
                ProjectBOM.project_id == project_id,
                ProjectBOM.is_active == True
            )
        )

        if parent_id is not None:
            query = query.filter(ProjectBOM.parent_bom_id == parent_id)
        elif level is not None:
            query = query.filter(ProjectBOM.level == level)

        return query.order_by(ProjectBOM.level, ProjectBOM.sequence).offset(skip).limit(limit).all()

    def update(self, bom_id: int, dto: ProjectBOMUpdateDTO) -> Optional[ProjectBOM]:
        """Update BOM item"""
        bom = self.get_by_id(bom_id)
        if not bom:
            return None

        if dto.description is not None:
            bom.description = dto.description
        if dto.part_number is not None:
            bom.part_number = dto.part_number
        if dto.part_description is not None:
            bom.part_description = dto.part_description
        if dto.quantity_required is not None:
            bom.quantity_required = dto.quantity_required
        if dto.quantity_allocated is not None:
            bom.quantity_allocated = dto.quantity_allocated
        if dto.quantity_issued is not None:
            bom.quantity_issued = dto.quantity_issued
        if dto.reference_designator is not None:
            bom.reference_designator = dto.reference_designator
        if dto.drawing_reference is not None:
            bom.drawing_reference = dto.drawing_reference
        if dto.find_number is not None:
            bom.find_number = dto.find_number
        if dto.procurement_status is not None:
            bom.procurement_status = dto.procurement_status
        if dto.supplier is not None:
            bom.supplier = dto.supplier
        if dto.lead_time_days is not None:
            bom.lead_time_days = dto.lead_time_days
        if dto.unit_cost is not None:
            bom.unit_cost = dto.unit_cost
        if dto.total_cost is not None:
            bom.total_cost = dto.total_cost
        elif dto.unit_cost is not None and bom.quantity_required:
            # Recalculate total cost
            bom.total_cost = dto.unit_cost * bom.quantity_required
        if dto.notes is not None:
            bom.notes = dto.notes
        if dto.special_instructions is not None:
            bom.special_instructions = dto.special_instructions
        if dto.is_critical is not None:
            bom.is_critical = dto.is_critical
        if dto.is_optional is not None:
            bom.is_optional = dto.is_optional
        if dto.is_active is not None:
            bom.is_active = dto.is_active

        self.db.commit()
        self.db.refresh(bom)
        return bom

    def delete(self, bom_id: int) -> bool:
        """Delete BOM item (soft delete)"""
        bom = self.get_by_id(bom_id)
        if not bom:
            return False

        bom.is_active = False
        self.db.commit()
        return True

    def get_bom_tree(self, project_id: int) -> List[ProjectBOM]:
        """Get hierarchical BOM tree for a project"""
        return self.db.query(ProjectBOM).filter(
            and_(
                ProjectBOM.project_id == project_id,
                ProjectBOM.is_active == True
            )
        ).order_by(ProjectBOM.level, ProjectBOM.parent_bom_id, ProjectBOM.sequence).all()
