"""
BOM (Bill of Materials) API endpoints.

Provides CRUD operations for BOM headers and lines, plus BOM tree explosion.
Supports multi-tenant isolation via RLS (organization_id, plant_id).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.dtos.bom_dto import (
    BOMHeaderCreateRequest,
    BOMHeaderUpdateRequest,
    BOMHeaderResponse,
    BOMLineCreateRequest,
    BOMLineUpdateRequest,
    BOMLineResponse,
    BOMListResponse
)
from app.models.bom import BOMHeader, BOMLine
from app.domain.entities.user import User


router = APIRouter()


# ============================================================================
# BOM Header Endpoints
# ============================================================================

@router.post("/", response_model=BOMHeaderResponse, status_code=status.HTTP_201_CREATED)
async def create_bom(
    bom: BOMHeaderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new BOM header.

    Validates:
    - Unique constraint: (organization_id, plant_id, material_id, bom_version)
    - Effective dates: end_date >= start_date
    - Base quantity > 0
    """
    # Validate effective dates
    if (bom.effective_start_date and bom.effective_end_date and
        bom.effective_end_date < bom.effective_start_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="effective_end_date must be >= effective_start_date"
        )

    # Check if BOM already exists for this material+version
    existing = db.query(BOMHeader).filter(
        BOMHeader.organization_id == bom.organization_id,
        BOMHeader.plant_id == bom.plant_id,
        BOMHeader.material_id == bom.material_id,
        BOMHeader.bom_version == bom.bom_version
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"BOM already exists for material {bom.material_id} version {bom.bom_version}"
        )

    try:
        db_bom = BOMHeader(**bom.model_dump())
        db.add(db_bom)
        db.commit()
        db.refresh(db_bom)
        return BOMHeaderResponse.model_validate(db_bom)
    except IntegrityError as e:
        db.rollback()
        if "foreign key" in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plant, material, or unit_of_measure reference"
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="BOM with this combination already exists"
        )


@router.get("/", response_model=BOMListResponse)
async def list_boms(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    material_id: Optional[int] = Query(None, description="Filter by material ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List BOMs with pagination and filters.

    RLS automatically filters by organization_id from JWT context.

    Query params:
    - page: Page number (default 1)
    - page_size: Items per page (default 50, max 100)
    - material_id: Filter by material
    - is_active: Filter by active status
    """
    # Build query with filters
    query = db.query(BOMHeader)

    if material_id is not None:
        query = query.filter(BOMHeader.material_id == material_id)

    if is_active is not None:
        query = query.filter(BOMHeader.is_active == is_active)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    boms = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return BOMListResponse(
        items=[BOMHeaderResponse.model_validate(bom) for bom in boms],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{bom_id}", response_model=BOMHeaderResponse)
async def get_bom(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get BOM detail by ID with all lines.

    Returns 404 if BOM not found or not accessible (RLS).
    """
    bom = db.query(BOMHeader).filter(BOMHeader.id == bom_id).first()

    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM not found"
        )

    return BOMHeaderResponse.model_validate(bom)


@router.put("/{bom_id}", response_model=BOMHeaderResponse)
async def update_bom(
    bom_id: int,
    bom_update: BOMHeaderUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update BOM header (partial update).

    Updatable fields:
    - bom_name
    - effective_start_date
    - effective_end_date
    - is_active

    Note: Cannot update material_id, bom_version (versioning constraint).
    """
    bom = db.query(BOMHeader).filter(BOMHeader.id == bom_id).first()

    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM not found"
        )

    # Update only provided fields
    update_data = bom_update.model_dump(exclude_unset=True)

    # Validate effective dates if both are being updated or exist
    if "effective_start_date" in update_data or "effective_end_date" in update_data:
        start_date = update_data.get("effective_start_date", bom.effective_start_date)
        end_date = update_data.get("effective_end_date", bom.effective_end_date)

        if start_date and end_date and end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="effective_end_date must be >= effective_start_date"
            )

    for field, value in update_data.items():
        setattr(bom, field, value)

    db.commit()
    db.refresh(bom)

    return BOMHeaderResponse.model_validate(bom)


@router.delete("/{bom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bom(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete BOM (set is_active=False).

    Does not delete BOM lines - they cascade with the header if hard deleted.
    """
    bom = db.query(BOMHeader).filter(BOMHeader.id == bom_id).first()

    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM not found"
        )

    bom.is_active = False
    db.commit()

    return None


# ============================================================================
# BOM Line Endpoints
# ============================================================================

@router.post("/{bom_id}/lines", response_model=BOMLineResponse, status_code=status.HTTP_201_CREATED)
async def add_bom_line(
    bom_id: int,
    line: BOMLineCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add component line to BOM.

    Validates:
    - BOM exists and is accessible
    - Unique line_number per BOM
    - Quantity > 0
    - Scrap factor 0-100%
    """
    # Verify BOM exists
    bom = db.query(BOMHeader).filter(BOMHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM not found"
        )

    # Ensure bom_header_id matches URL parameter
    if line.bom_header_id != bom_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bom_header_id in body must match URL parameter"
        )

    # Check for duplicate line_number
    existing_line = db.query(BOMLine).filter(
        BOMLine.bom_header_id == bom_id,
        BOMLine.line_number == line.line_number
    ).first()

    if existing_line:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Line number {line.line_number} already exists in this BOM"
        )

    try:
        db_line = BOMLine(**line.model_dump())
        db.add(db_line)
        db.commit()
        db.refresh(db_line)
        return BOMLineResponse.model_validate(db_line)
    except IntegrityError as e:
        db.rollback()
        if "foreign key" in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid component_material or unit_of_measure reference"
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="BOM line with this line_number already exists"
        )


@router.put("/{bom_id}/lines/{line_id}", response_model=BOMLineResponse)
async def update_bom_line(
    bom_id: int,
    line_id: int,
    line_update: BOMLineUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update BOM line.

    Updatable fields:
    - quantity
    - scrap_factor
    - operation_number
    - is_phantom
    - backflush

    Note: Cannot change component_material_id or line_number (integrity constraint).
    """
    # Verify BOM exists
    bom = db.query(BOMHeader).filter(BOMHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM not found"
        )

    # Get line
    line = db.query(BOMLine).filter(
        BOMLine.id == line_id,
        BOMLine.bom_header_id == bom_id
    ).first()

    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM line not found"
        )

    # Update fields
    update_data = line_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(line, field, value)

    try:
        db.commit()
        db.refresh(line)
        return BOMLineResponse.model_validate(line)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid update: constraint violation"
        )


@router.delete("/{bom_id}/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bom_line(
    bom_id: int,
    line_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete BOM line (hard delete).

    Removes component from BOM permanently.
    """
    # Verify BOM exists
    bom = db.query(BOMHeader).filter(BOMHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM not found"
        )

    # Get line
    line = db.query(BOMLine).filter(
        BOMLine.id == line_id,
        BOMLine.bom_header_id == bom_id
    ).first()

    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM line not found"
        )

    db.delete(line)
    db.commit()

    return None


# ============================================================================
# BOM Tree Explosion Endpoint
# ============================================================================

@router.get("/{bom_id}/tree")
async def get_bom_tree(
    bom_id: int,
    max_levels: int = Query(10, ge=1, le=20, description="Maximum recursion depth"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get multi-level BOM tree explosion.

    Recursively expands all component levels to show complete material requirements.

    Example structure:
    {
      "material_id": 1,
      "bom_id": 1,
      "bom_version": 1,
      "components": [
        {
          "line_id": 1,
          "component_material_id": 2,
          "quantity": 1.0,
          "scrap_factor": 5.0,
          "level": 1,
          "components": [
            {
              "line_id": 5,
              "component_material_id": 10,
              "quantity": 3.0,
              "level": 2,
              "components": []
            }
          ]
        }
      ]
    }

    Query params:
    - max_levels: Maximum recursion depth (default 10, max 20)
      Prevents infinite loops in circular BOMs.
    """
    # Verify BOM exists
    bom = db.query(BOMHeader).filter(BOMHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM not found"
        )

    def build_tree(material_id: int, level: int = 0, visited: set = None) -> Optional[dict]:
        """
        Recursively build BOM tree.

        Args:
            material_id: Material to explode
            level: Current recursion level
            visited: Set of material_ids to prevent circular references

        Returns:
            Tree structure dict or None if no BOM exists
        """
        if visited is None:
            visited = set()

        # Prevent infinite recursion
        if level >= max_levels:
            return None

        # Prevent circular references
        if material_id in visited:
            return None

        visited.add(material_id)

        # Get active BOM for this material
        material_bom = db.query(BOMHeader).filter(
            BOMHeader.material_id == material_id,
            BOMHeader.is_active == True
        ).order_by(BOMHeader.bom_version.desc()).first()

        if not material_bom:
            return None

        tree = {
            "material_id": material_id,
            "bom_id": material_bom.id,
            "bom_version": material_bom.bom_version,
            "components": []
        }

        # Get all components (BOM lines)
        for line in material_bom.bom_lines:
            component = {
                "line_id": line.id,
                "component_material_id": line.component_material_id,
                "quantity": float(line.quantity),
                "scrap_factor": float(line.scrap_factor) if line.scrap_factor else 0.0,
                "level": level + 1,
                "is_phantom": line.is_phantom,
                "backflush": line.backflush
            }

            # Recursively get sub-components
            subtree = build_tree(
                line.component_material_id,
                level + 1,
                visited.copy()  # Copy to allow same component in different branches
            )

            if subtree and subtree.get("components"):
                component["components"] = subtree["components"]
            else:
                component["components"] = []

            tree["components"].append(component)

        return tree

    tree = build_tree(bom.material_id)

    if not tree:
        # Return minimal structure if no components
        return {
            "material_id": bom.material_id,
            "bom_id": bom.id,
            "bom_version": bom.bom_version,
            "components": []
        }

    return tree
