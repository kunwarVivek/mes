"""
API endpoints for Configuration Engine (Custom Fields and Type Lists)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.services.custom_field_service import CustomFieldService
from app.application.dtos.custom_field_dto import (
    CustomFieldCreateDTO,
    CustomFieldUpdateDTO,
    CustomFieldResponse,
    FieldValueSetDTO,
    FieldValueResponse,
    FieldValuesBulkSetDTO,
    TypeListCreateDTO,
    TypeListUpdateDTO,
    TypeListResponse,
    TypeListValueCreateDTO,
    TypeListValueResponse,
)

router = APIRouter(prefix="/custom-fields", tags=["configuration-engine"])


# ========== Custom Field Management Endpoints ==========

@router.post("/", response_model=CustomFieldResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_field(
    dto: CustomFieldCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new custom field for an entity type.

    **Allows organizations to add custom fields to any entity** (materials, work orders, etc.)
    without code changes.

    **Field Types:**
    - text, textarea, email, url, phone
    - number, date, datetime
    - select, multiselect (requires options)
    - boolean, file

    **Validation Rules:**
    - min_length, max_length, pattern (for text)
    - min_value, max_value (for number)
    - allowed_file_types (for file)
    - date_range (for date/datetime)
    """
    service = CustomFieldService(db)
    created_by = current_user.get("id")

    try:
        field = service.create_custom_field(dto, created_by)
        return CustomFieldResponse.model_validate(field)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[CustomFieldResponse])
async def list_custom_fields(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    include_inactive: bool = Query(False, description="Include inactive fields"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all custom fields for current organization.

    **Query Params:**
    - entity_type: Filter by entity type (material, work_order, etc.)
    - include_inactive: Include inactive fields
    - skip: Pagination offset
    - limit: Max results
    """
    service = CustomFieldService(db)
    organization_id = current_user.get("organization_id")

    if entity_type:
        fields = service.list_custom_fields(organization_id, entity_type, include_inactive, skip, limit)
    else:
        fields = service.list_all_custom_fields(organization_id, entity_type, skip, limit)

    return [CustomFieldResponse.model_validate(field) for field in fields]


@router.get("/{field_id}", response_model=CustomFieldResponse)
async def get_custom_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get custom field by ID"""
    service = CustomFieldService(db)
    field = service.get_custom_field(field_id)

    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom field not found")

    return CustomFieldResponse.model_validate(field)


@router.put("/{field_id}", response_model=CustomFieldResponse)
async def update_custom_field(
    field_id: int,
    dto: CustomFieldUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a custom field.

    **Note:** Cannot change field_code or field_type after creation.
    """
    service = CustomFieldService(db)

    try:
        field = service.update_custom_field(field_id, dto)
        if not field:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom field not found")

        return CustomFieldResponse.model_validate(field)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a custom field.

    **Warning:** This will cascade delete all field values for this field.
    """
    service = CustomFieldService(db)

    success = service.delete_custom_field(field_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom field not found")


# ========== Field Value Endpoints ==========

@router.get("/entity/{entity_type}/{entity_id}/values", response_model=List[FieldValueResponse])
async def get_entity_field_values(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all custom field values for an entity instance.

    **Example:** GET /custom-fields/entity/material/123/values
    Returns all custom field values for material #123
    """
    service = CustomFieldService(db)
    field_values = service.get_entity_field_values(entity_type, entity_id)

    return [FieldValueResponse.model_validate(fv) for fv in field_values]


@router.put("/entity/{entity_type}/{entity_id}/values", response_model=List[FieldValueResponse])
async def set_entity_field_values(
    entity_type: str,
    entity_id: int,
    field_values: List[FieldValueSetDTO],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Set multiple custom field values for an entity instance.

    **Example:**
    ```json
    [
      {"custom_field_id": 1, "value": 45},
      {"custom_field_id": 2, "value": "High"}
    ]
    ```

    **Validation:**
    - All values are validated against field rules
    - If any validation fails, no values are set (atomic operation)
    """
    service = CustomFieldService(db)
    organization_id = current_user.get("organization_id")

    dto = FieldValuesBulkSetDTO(
        entity_type=entity_type,
        entity_id=entity_id,
        field_values=field_values
    )

    try:
        result = service.bulk_set_field_values(organization_id, dto)
        return [FieldValueResponse.model_validate(fv) for fv in result]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/schema/{entity_type}")
async def get_entity_field_schema(
    entity_type: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the complete custom field schema for an entity type.

    **Returns:** JSON schema-like structure describing all custom fields.

    **Use Case:** Frontend form generation - build dynamic forms from schema
    """
    service = CustomFieldService(db)
    organization_id = current_user.get("organization_id")

    return service.get_field_schema(organization_id, entity_type)


# ========== Type List Management Endpoints ==========

type_list_router = APIRouter(prefix="/type-lists", tags=["configuration-engine"])


@type_list_router.post("/", response_model=TypeListResponse, status_code=status.HTTP_201_CREATED)
async def create_type_list(
    dto: TypeListCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new type list (configurable taxonomy).

    **Examples:**
    - NCR severity levels
    - Defect types
    - Work order priorities
    - Custom status values

    **Features:**
    - Each list has a unique code
    - Values have codes, labels, and optional metadata (color, icon, etc.)
    - Can mark lists as allowing custom values
    """
    service = CustomFieldService(db)
    created_by = current_user.get("id")

    try:
        type_list = service.create_type_list(dto, created_by)
        return TypeListResponse.model_validate(type_list)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@type_list_router.get("/", response_model=List[TypeListResponse])
async def list_type_lists(
    category: Optional[str] = Query(None, description="Filter by category"),
    include_inactive: bool = Query(False, description="Include inactive lists"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all type lists for current organization.

    **Query Params:**
    - category: Filter by category (quality, production, etc.)
    - include_inactive: Include inactive lists
    """
    service = CustomFieldService(db)
    organization_id = current_user.get("organization_id")

    type_lists = service.list_type_lists(organization_id, category, include_inactive, skip, limit)
    return [TypeListResponse.model_validate(tl) for tl in type_lists]


@type_list_router.get("/{list_code}", response_model=TypeListResponse)
async def get_type_list(
    list_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get type list by code with all its values.

    **Example:** GET /type-lists/NCR_SEVERITY
    """
    service = CustomFieldService(db)
    organization_id = current_user.get("organization_id")

    type_list = service.get_type_list_with_values(organization_id, list_code)

    if not type_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type list not found")

    return TypeListResponse.model_validate(type_list)


@type_list_router.put("/{type_list_id}", response_model=TypeListResponse)
async def update_type_list(
    type_list_id: int,
    dto: TypeListUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update type list.

    **Note:** System type lists cannot be modified.
    """
    service = CustomFieldService(db)

    try:
        type_list = service.update_type_list(type_list_id, dto)
        if not type_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type list not found")

        return TypeListResponse.model_validate(type_list)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@type_list_router.delete("/{type_list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_type_list(
    type_list_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete type list.

    **Note:**
    - System type lists cannot be deleted
    - Cascades to delete all values
    """
    service = CustomFieldService(db)

    try:
        success = service.delete_type_list(type_list_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type list not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== Type List Value Endpoints ==========

@type_list_router.post("/{type_list_id}/values", response_model=TypeListValueResponse,
                      status_code=status.HTTP_201_CREATED)
async def add_type_list_value(
    type_list_id: int,
    dto: TypeListValueCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a value to a type list.

    **Metadata Examples:**
    ```json
    {
      "color": "#FF0000",
      "icon": "alert-triangle",
      "severity": "high",
      "requires_approval": true
    }
    ```
    """
    service = CustomFieldService(db)
    organization_id = current_user.get("organization_id")

    # Override type_list_id from path
    dto.type_list_id = type_list_id

    try:
        value = service.add_type_list_value(organization_id, dto)
        return TypeListValueResponse.model_validate(value)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@type_list_router.get("/{type_list_id}/values", response_model=List[TypeListValueResponse])
async def get_type_list_values(
    type_list_id: int,
    include_inactive: bool = Query(False, description="Include inactive values"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all values for a type list"""
    service = CustomFieldService(db)

    values = service.get_type_list_values(type_list_id, include_inactive)
    return [TypeListValueResponse.model_validate(v) for v in values]


@type_list_router.put("/values/{value_id}", response_model=TypeListValueResponse)
async def update_type_list_value(
    value_id: int,
    updates: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update type list value"""
    service = CustomFieldService(db)

    try:
        value = service.update_type_list_value(value_id, updates)
        if not value:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Value not found")

        return TypeListValueResponse.model_validate(value)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@type_list_router.delete("/values/{value_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_type_list_value(
    value_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete type list value"""
    service = CustomFieldService(db)

    success = service.delete_type_list_value(value_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Value not found")


# Include both routers
router.include_router(type_list_router)
