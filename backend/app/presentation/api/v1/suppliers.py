"""Suppliers API endpoints for material procurement management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.supplier import Supplier
from app.presentation.middleware.auth_middleware import get_current_user
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


# Pydantic Schemas
class SupplierBase(BaseModel):
    supplier_code: str = Field(..., min_length=1, max_length=100, description="Unique supplier code")
    name: str = Field(..., min_length=1, max_length=255, description="Supplier name")
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    payment_terms: Optional[str] = Field(None, max_length=100, description="e.g., Net 30, Net 60")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Supplier rating (1-5 stars)")
    is_active: bool = True
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    supplier_code: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    payment_terms: Optional[str] = Field(None, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: int
    organization_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# API Endpoints
@router.get("", response_model=List[SupplierResponse])
def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search in name, code, city"),
    rating_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating filter"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all suppliers with pagination and filtering.

    Filters:
    - search: Search in supplier name, code, or city
    - rating_min: Minimum supplier rating (1-5)
    - is_active: Filter by active/inactive status
    """
    organization_id = current_user["organization_id"]

    query = db.query(Supplier).filter(Supplier.organization_id == organization_id)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Supplier.name.ilike(search_term),
                Supplier.supplier_code.ilike(search_term),
                Supplier.city.ilike(search_term)
            )
        )

    if rating_min is not None:
        query = query.filter(Supplier.rating >= rating_min)

    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)

    # Order by name and paginate
    suppliers = query.order_by(Supplier.name).offset(skip).limit(limit).all()

    return suppliers


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific supplier by ID."""
    organization_id = current_user["organization_id"]

    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.organization_id == organization_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    return supplier


@router.post("", response_model=SupplierResponse, status_code=201)
def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new supplier.

    Validations:
    - Supplier code must be unique within organization
    - Rating must be between 1 and 5 if provided
    """
    organization_id = current_user["organization_id"]

    # Check for duplicate supplier code
    existing_supplier = db.query(Supplier).filter(
        Supplier.organization_id == organization_id,
        Supplier.supplier_code == supplier_data.supplier_code
    ).first()

    if existing_supplier:
        raise HTTPException(
            status_code=400,
            detail=f"Supplier with code '{supplier_data.supplier_code}' already exists"
        )

    # Create supplier
    supplier = Supplier(
        organization_id=organization_id,
        **supplier_data.dict()
    )

    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing supplier.

    Partial updates are supported - only provided fields will be updated.
    """
    organization_id = current_user["organization_id"]

    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.organization_id == organization_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Check for duplicate supplier code if being updated
    if supplier_data.supplier_code and supplier_data.supplier_code != supplier.supplier_code:
        existing_supplier = db.query(Supplier).filter(
            Supplier.organization_id == organization_id,
            Supplier.supplier_code == supplier_data.supplier_code,
            Supplier.id != supplier_id
        ).first()

        if existing_supplier:
            raise HTTPException(
                status_code=400,
                detail=f"Supplier with code '{supplier_data.supplier_code}' already exists"
            )

    # Update fields
    update_data = supplier_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)

    return supplier


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a supplier.

    Note: This is a hard delete. Consider soft delete (is_active=false) for audit trail.
    """
    organization_id = current_user["organization_id"]

    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.organization_id == organization_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Check if supplier is referenced by materials or NCRs
    # TODO: Add validation to prevent deletion if supplier is referenced

    db.delete(supplier)
    db.commit()

    return None


@router.get("/{supplier_id}/materials")
def get_supplier_materials(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all materials associated with this supplier."""
    organization_id = current_user["organization_id"]

    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.organization_id == organization_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # TODO: Query material_suppliers table when it exists
    return {
        "supplier_id": supplier_id,
        "materials": []  # Placeholder
    }


@router.post("/{supplier_id}/rate")
def rate_supplier(
    supplier_id: int,
    rating: int = Query(..., ge=1, le=5, description="Supplier rating (1-5 stars)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Rate a supplier (1-5 stars).

    This updates the supplier's rating field.
    """
    organization_id = current_user["organization_id"]

    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.organization_id == organization_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    supplier.rating = rating
    db.commit()
    db.refresh(supplier)

    return {"supplier_id": supplier_id, "rating": rating, "message": "Supplier rated successfully"}
