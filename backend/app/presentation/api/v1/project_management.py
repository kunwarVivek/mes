"""
API endpoints for Project Management (Documents, Milestones, RDA, BOM)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.services.project_management_service import (
    ProjectDocumentService,
    ProjectMilestoneService,
    RDADrawingService,
    ProjectBOMService,
)
from app.application.dtos.project_management_dto import (
    ProjectDocumentCreateDTO,
    ProjectDocumentUpdateDTO,
    ProjectDocumentResponse,
    ProjectMilestoneCreateDTO,
    ProjectMilestoneUpdateDTO,
    ProjectMilestoneResponse,
    RDADrawingCreateDTO,
    RDADrawingUpdateDTO,
    RDADrawingSubmitDTO,
    RDADrawingReviewDTO,
    RDADrawingResponse,
    ProjectBOMCreateDTO,
    ProjectBOMUpdateDTO,
    ProjectBOMResponse,
    DocumentVersionCreateDTO,
    MilestoneProgressUpdateDTO,
)

router = APIRouter()


# ========== Project Document Endpoints ==========

@router.post("/projects/{project_id}/documents", response_model=ProjectDocumentResponse,
            status_code=status.HTTP_201_CREATED, tags=["project-documents"])
async def create_project_document(
    project_id: int,
    dto: ProjectDocumentCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new project document"""
    service = ProjectDocumentService(db)
    uploaded_by = current_user.get("id")

    # Override project_id from path
    dto.project_id = project_id
    dto.organization_id = current_user.get("organization_id")

    document = service.create_document(dto, uploaded_by)
    return ProjectDocumentResponse.from_orm(document)


@router.get("/projects/{project_id}/documents", response_model=List[ProjectDocumentResponse],
           tags=["project-documents"])
async def list_project_documents(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    latest_only: bool = Query(True, description="Show only latest versions"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List documents for a project"""
    service = ProjectDocumentService(db)

    documents = service.list_documents(project_id, skip, limit, latest_only, document_type)
    return [ProjectDocumentResponse.from_orm(doc) for doc in documents]


@router.get("/documents/{document_id}", response_model=ProjectDocumentResponse, tags=["project-documents"])
async def get_project_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get document by ID"""
    service = ProjectDocumentService(db)

    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return ProjectDocumentResponse.from_orm(document)


@router.get("/documents/{document_id}/versions", response_model=List[ProjectDocumentResponse],
           tags=["project-documents"])
async def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all versions of a document"""
    service = ProjectDocumentService(db)

    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    versions = service.get_document_versions(document.document_code, document.project_id)
    return [ProjectDocumentResponse.from_orm(doc) for doc in versions]


@router.post("/documents/{document_id}/versions", response_model=ProjectDocumentResponse,
            status_code=status.HTTP_201_CREATED, tags=["project-documents"])
async def create_document_version(
    document_id: int,
    dto: DocumentVersionCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new version of an existing document"""
    service = ProjectDocumentService(db)
    uploaded_by = current_user.get("id")

    try:
        new_version = service.create_document_version(document_id, dto, uploaded_by)
        return ProjectDocumentResponse.from_orm(new_version)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/documents/{document_id}", response_model=ProjectDocumentResponse, tags=["project-documents"])
async def update_project_document(
    document_id: int,
    dto: ProjectDocumentUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update document"""
    service = ProjectDocumentService(db)

    document = service.update_document(document_id, dto)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return ProjectDocumentResponse.from_orm(document)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["project-documents"])
async def delete_project_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete document (soft delete)"""
    service = ProjectDocumentService(db)

    success = service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


@router.post("/documents/{document_id}/archive", response_model=ProjectDocumentResponse, tags=["project-documents"])
async def archive_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Archive a document"""
    service = ProjectDocumentService(db)

    document = service.archive_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return ProjectDocumentResponse.from_orm(document)


# ========== Project Milestone Endpoints ==========

@router.post("/projects/{project_id}/milestones", response_model=ProjectMilestoneResponse,
            status_code=status.HTTP_201_CREATED, tags=["project-milestones"])
async def create_project_milestone(
    project_id: int,
    dto: ProjectMilestoneCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new project milestone"""
    service = ProjectMilestoneService(db)

    # Override project_id from path
    dto.project_id = project_id
    dto.organization_id = current_user.get("organization_id")

    milestone = service.create_milestone(dto)
    return ProjectMilestoneResponse.from_orm(milestone)


@router.get("/projects/{project_id}/milestones", response_model=List[ProjectMilestoneResponse],
           tags=["project-milestones"])
async def list_project_milestones(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    critical_only: bool = Query(False, description="Show only critical path"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List milestones for a project"""
    service = ProjectMilestoneService(db)

    milestones = service.list_milestones(project_id, skip, limit, status, critical_only)
    return [ProjectMilestoneResponse.from_orm(m) for m in milestones]


@router.get("/projects/{project_id}/milestones/overdue", response_model=List[ProjectMilestoneResponse],
           tags=["project-milestones"])
async def get_overdue_milestones(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get overdue milestones for a project"""
    service = ProjectMilestoneService(db)

    milestones = service.get_overdue_milestones(project_id)
    return [ProjectMilestoneResponse.from_orm(m) for m in milestones]


@router.get("/projects/{project_id}/milestones/critical-path", response_model=List[ProjectMilestoneResponse],
           tags=["project-milestones"])
async def get_critical_path_milestones(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get critical path milestones"""
    service = ProjectMilestoneService(db)

    milestones = service.get_critical_path(project_id)
    return [ProjectMilestoneResponse.from_orm(m) for m in milestones]


@router.get("/milestones/{milestone_id}", response_model=ProjectMilestoneResponse, tags=["project-milestones"])
async def get_project_milestone(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get milestone by ID"""
    service = ProjectMilestoneService(db)

    milestone = service.get_milestone(milestone_id)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    return ProjectMilestoneResponse.from_orm(milestone)


@router.put("/milestones/{milestone_id}", response_model=ProjectMilestoneResponse, tags=["project-milestones"])
async def update_project_milestone(
    milestone_id: int,
    dto: ProjectMilestoneUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update milestone"""
    service = ProjectMilestoneService(db)

    milestone = service.update_milestone(milestone_id, dto)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    return ProjectMilestoneResponse.from_orm(milestone)


@router.post("/milestones/{milestone_id}/progress", response_model=ProjectMilestoneResponse,
            tags=["project-milestones"])
async def update_milestone_progress(
    milestone_id: int,
    dto: MilestoneProgressUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update milestone progress"""
    service = ProjectMilestoneService(db)

    milestone = service.update_progress(milestone_id, dto)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    return ProjectMilestoneResponse.from_orm(milestone)


@router.post("/milestones/{milestone_id}/complete", response_model=ProjectMilestoneResponse,
            tags=["project-milestones"])
async def complete_milestone(
    milestone_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark milestone as completed"""
    service = ProjectMilestoneService(db)

    milestone = service.complete_milestone(milestone_id, notes)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    return ProjectMilestoneResponse.from_orm(milestone)


@router.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["project-milestones"])
async def delete_project_milestone(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete milestone (soft delete)"""
    service = ProjectMilestoneService(db)

    success = service.delete_milestone(milestone_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")


# ========== RDA Drawing Endpoints ==========

@router.post("/projects/{project_id}/rda", response_model=RDADrawingResponse,
            status_code=status.HTTP_201_CREATED, tags=["rda"])
async def create_rda_drawing(
    project_id: int,
    dto: RDADrawingCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new RDA (Request for Drawing Approval)"""
    service = RDADrawingService(db)
    submitted_by = current_user.get("id")

    # Override project_id from path
    dto.project_id = project_id
    dto.organization_id = current_user.get("organization_id")

    rda = service.create_rda(dto, submitted_by)
    return RDADrawingResponse.from_orm(rda)


@router.get("/projects/{project_id}/rda", response_model=List[RDADrawingResponse], tags=["rda"])
async def list_rda_drawings(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    approval_status: Optional[str] = Query(None, description="Filter by approval status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List RDA drawings for a project"""
    service = RDADrawingService(db)

    rdas = service.list_rdas(project_id, skip, limit, approval_status)
    return [RDADrawingResponse.from_orm(rda) for rda in rdas]


@router.get("/projects/{project_id}/rda/pending-approvals", response_model=List[RDADrawingResponse], tags=["rda"])
async def get_pending_rda_approvals(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get RDAs pending approval by current user"""
    service = RDADrawingService(db)
    user_id = current_user.get("id")

    rdas = service.get_pending_approvals(project_id, user_id)
    return [RDADrawingResponse.from_orm(rda) for rda in rdas]


@router.get("/rda/{rda_id}", response_model=RDADrawingResponse, tags=["rda"])
async def get_rda_drawing(
    rda_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get RDA by ID"""
    service = RDADrawingService(db)

    rda = service.get_rda(rda_id)
    if not rda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RDA not found")

    return RDADrawingResponse.from_orm(rda)


@router.put("/rda/{rda_id}", response_model=RDADrawingResponse, tags=["rda"])
async def update_rda_drawing(
    rda_id: int,
    dto: RDADrawingUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update RDA (only in DRAFT status)"""
    service = RDADrawingService(db)

    try:
        rda = service.update_rda(rda_id, dto)
        if not rda:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RDA not found")
        return RDADrawingResponse.from_orm(rda)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/rda/{rda_id}/submit", response_model=RDADrawingResponse, tags=["rda"])
async def submit_rda_for_approval(
    rda_id: int,
    dto: RDADrawingSubmitDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit RDA for approval"""
    service = RDADrawingService(db)

    try:
        rda = service.submit_for_approval(rda_id, dto)
        if not rda:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RDA not found")
        return RDADrawingResponse.from_orm(rda)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/rda/{rda_id}/review", response_model=RDADrawingResponse, tags=["rda"])
async def review_rda_drawing(
    rda_id: int,
    dto: RDADrawingReviewDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Review RDA (approve or reject)"""
    service = RDADrawingService(db)
    user_id = current_user.get("id")

    try:
        rda = service.review_rda(rda_id, dto, user_id)
        if not rda:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RDA not found")
        return RDADrawingResponse.from_orm(rda)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== Project BOM Endpoints ==========

@router.post("/projects/{project_id}/bom", response_model=ProjectBOMResponse,
            status_code=status.HTTP_201_CREATED, tags=["project-bom"])
async def create_project_bom_item(
    project_id: int,
    dto: ProjectBOMCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new project BOM item"""
    service = ProjectBOMService(db)

    # Override project_id from path
    dto.project_id = project_id
    dto.organization_id = current_user.get("organization_id")

    bom_item = service.create_bom_item(dto)
    return ProjectBOMResponse.from_orm(bom_item)


@router.get("/projects/{project_id}/bom", response_model=List[ProjectBOMResponse], tags=["project-bom"])
async def list_project_bom_items(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    parent_id: Optional[int] = Query(None, description="Filter by parent BOM ID"),
    level: Optional[int] = Query(None, description="Filter by BOM level"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List BOM items for a project"""
    service = ProjectBOMService(db)

    bom_items = service.list_bom_items(project_id, skip, limit, parent_id, level)
    return [ProjectBOMResponse.from_orm(item) for item in bom_items]


@router.get("/projects/{project_id}/bom/tree", response_model=List[ProjectBOMResponse], tags=["project-bom"])
async def get_project_bom_tree(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get hierarchical BOM tree"""
    service = ProjectBOMService(db)

    bom_tree = service.get_bom_tree(project_id)
    return [ProjectBOMResponse.from_orm(item) for item in bom_tree]


@router.get("/projects/{project_id}/bom/critical", response_model=List[ProjectBOMResponse], tags=["project-bom"])
async def get_critical_bom_items(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get critical BOM items"""
    service = ProjectBOMService(db)

    critical_items = service.get_critical_items(project_id)
    return [ProjectBOMResponse.from_orm(item) for item in critical_items]


@router.get("/projects/{project_id}/bom/summary", tags=["project-bom"])
async def get_bom_procurement_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get procurement summary for project BOM"""
    service = ProjectBOMService(db)
    return service.get_procurement_summary(project_id)


@router.get("/bom/{bom_id}", response_model=ProjectBOMResponse, tags=["project-bom"])
async def get_project_bom_item(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get BOM item by ID"""
    service = ProjectBOMService(db)

    bom_item = service.get_bom_item(bom_id)
    if not bom_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BOM item not found")

    return ProjectBOMResponse.from_orm(bom_item)


@router.put("/bom/{bom_id}", response_model=ProjectBOMResponse, tags=["project-bom"])
async def update_project_bom_item(
    bom_id: int,
    dto: ProjectBOMUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update BOM item"""
    service = ProjectBOMService(db)

    bom_item = service.update_bom_item(bom_id, dto)
    if not bom_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BOM item not found")

    return ProjectBOMResponse.from_orm(bom_item)


@router.post("/bom/{bom_id}/allocate", response_model=ProjectBOMResponse, tags=["project-bom"])
async def allocate_bom_quantity(
    bom_id: int,
    quantity: float = Query(..., gt=0, description="Quantity to allocate"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Allocate quantity to BOM item"""
    service = ProjectBOMService(db)

    try:
        bom_item = service.allocate_quantity(bom_id, quantity)
        if not bom_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BOM item not found")
        return ProjectBOMResponse.from_orm(bom_item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bom/{bom_id}/issue", response_model=ProjectBOMResponse, tags=["project-bom"])
async def issue_bom_quantity(
    bom_id: int,
    quantity: float = Query(..., gt=0, description="Quantity to issue"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Issue quantity from BOM item"""
    service = ProjectBOMService(db)

    try:
        bom_item = service.issue_quantity(bom_id, quantity)
        if not bom_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BOM item not found")
        return ProjectBOMResponse.from_orm(bom_item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/bom/{bom_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["project-bom"])
async def delete_project_bom_item(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete BOM item (soft delete)"""
    service = ProjectBOMService(db)

    success = service.delete_bom_item(bom_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BOM item not found")
