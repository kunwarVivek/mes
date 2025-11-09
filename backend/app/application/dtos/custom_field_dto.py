"""
DTOs for Configuration Engine (Custom Fields and Type Lists)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime


# ========== CustomField DTOs ==========

class CustomFieldCreateDTO(BaseModel):
    """DTO for creating a new custom field"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    entity_type: str = Field(..., min_length=1, max_length=50, description="Entity type (material, work_order, etc.)")
    field_name: str = Field(..., min_length=1, max_length=100, description="Field name")
    field_code: str = Field(..., min_length=1, max_length=50, description="Unique field code (snake_case)")
    field_label: str = Field(..., min_length=1, max_length=100, description="Display label")
    field_type: str = Field(..., description="Field type (text, number, date, select, etc.)")
    description: Optional[str] = Field(None, description="Field description")
    default_value: Optional[str] = Field(None, description="Default value")
    is_required: bool = Field(default=False, description="Is field required")
    is_active: bool = Field(default=True, description="Is field active")
    display_order: int = Field(default=0, description="Display order")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules JSON")
    options: Optional[List[Dict[str, Any]]] = Field(None, description="Options for select/multiselect fields")
    ui_config: Optional[Dict[str, Any]] = Field(None, description="UI configuration JSON")

    @field_validator('field_code')
    @classmethod
    def validate_field_code(cls, v):
        """Ensure field_code is lowercase with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('field_code must be alphanumeric with underscores')
        return v.lower()

    @field_validator('field_type')
    @classmethod
    def validate_field_type(cls, v):
        """Validate field type"""
        valid_types = [
            'text', 'number', 'date', 'datetime', 'select', 'multiselect',
            'boolean', 'file', 'textarea', 'email', 'url', 'phone'
        ]
        if v not in valid_types:
            raise ValueError(f'field_type must be one of {valid_types}')
        return v

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
                "entity_type": "material",
                "field_name": "Shelf Life Days",
                "field_code": "shelf_life_days",
                "field_label": "Shelf Life (Days)",
                "field_type": "number",
                "description": "Number of days product can be stored",
                "default_value": "30",
                "is_required": False,
                "is_active": True,
                "display_order": 1,
                "validation_rules": {
                    "min_value": 1,
                    "max_value": 365
                },
                "options": None,
                "ui_config": {
                    "placeholder": "Enter shelf life in days",
                    "help_text": "Standard shelf life for this material"
                }
            }
        }


class CustomFieldUpdateDTO(BaseModel):
    """DTO for updating an existing custom field"""
    field_name: Optional[str] = Field(None, min_length=1, max_length=100)
    field_label: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    default_value: Optional[str] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, Any]]] = None
    ui_config: Optional[Dict[str, Any]] = None


class CustomFieldResponse(BaseModel):
    """DTO for custom field response"""
    id: int
    organization_id: int
    entity_type: str
    field_name: str
    field_code: str
    field_label: str
    field_type: str
    description: Optional[str] = None
    default_value: Optional[str] = None
    is_required: bool
    is_active: bool
    display_order: int
    validation_rules: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, Any]]] = None
    ui_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "entity_type": "material",
                "field_name": "Shelf Life Days",
                "field_code": "shelf_life_days",
                "field_label": "Shelf Life (Days)",
                "field_type": "number",
                "description": "Number of days product can be stored",
                "default_value": "30",
                "is_required": False,
                "is_active": True,
                "display_order": 1,
                "validation_rules": {"min_value": 1, "max_value": 365},
                "options": None,
                "ui_config": {"placeholder": "Enter shelf life in days"},
                "created_at": "2025-11-09T10:00:00Z",
                "updated_at": None,
                "created_by": 1
            }
        }


# ========== FieldValue DTOs ==========

class FieldValueSetDTO(BaseModel):
    """DTO for setting a field value"""
    custom_field_id: int = Field(..., gt=0, description="Custom field ID")
    value: Any = Field(..., description="Field value (string, number, boolean, array, object)")

    class Config:
        json_schema_extra = {
            "example": {
                "custom_field_id": 1,
                "value": 45
            }
        }


class FieldValueResponse(BaseModel):
    """DTO for field value response"""
    id: int
    organization_id: int
    custom_field_id: int
    entity_type: str
    entity_id: int
    value: Any
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Nested custom field details
    custom_field: Optional[CustomFieldResponse] = None

    class Config:
        from_attributes = True


class FieldValuesBulkSetDTO(BaseModel):
    """DTO for setting multiple field values at once"""
    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_id: int = Field(..., gt=0)
    field_values: List[FieldValueSetDTO] = Field(..., min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "material",
                "entity_id": 123,
                "field_values": [
                    {"custom_field_id": 1, "value": 45},
                    {"custom_field_id": 2, "value": "High"}
                ]
            }
        }


# ========== TypeList DTOs ==========

class TypeListCreateDTO(BaseModel):
    """DTO for creating a new type list"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    list_name: str = Field(..., min_length=1, max_length=100, description="List name")
    list_code: str = Field(..., min_length=1, max_length=50, description="Unique list code")
    description: Optional[str] = Field(None, description="List description")
    category: Optional[str] = Field(None, max_length=50, description="Category (quality, production, etc.)")
    allow_custom_values: bool = Field(default=False, description="Allow users to add custom values")

    @field_validator('list_code')
    @classmethod
    def validate_list_code(cls, v):
        """Ensure list_code is uppercase and alphanumeric with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('list_code must be alphanumeric with underscores')
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "list_name": "NCR Severity Levels",
                "list_code": "NCR_SEVERITY",
                "description": "Severity levels for non-conformance reports",
                "category": "quality",
                "allow_custom_values": False
            }
        }


class TypeListUpdateDTO(BaseModel):
    """DTO for updating an existing type list"""
    list_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    allow_custom_values: Optional[bool] = None


class TypeListResponse(BaseModel):
    """DTO for type list response"""
    id: int
    organization_id: int
    list_name: str
    list_code: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_system_list: bool
    is_active: bool
    allow_custom_values: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    # Nested values (optional, for detailed response)
    values: Optional[List['TypeListValueResponse']] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "list_name": "NCR Severity Levels",
                "list_code": "NCR_SEVERITY",
                "description": "Severity levels for non-conformance reports",
                "category": "quality",
                "is_system_list": False,
                "is_active": True,
                "allow_custom_values": False,
                "created_at": "2025-11-09T10:00:00Z",
                "updated_at": None,
                "created_by": 1,
                "values": []
            }
        }


# ========== TypeListValue DTOs ==========

class TypeListValueCreateDTO(BaseModel):
    """DTO for creating a type list value"""
    type_list_id: int = Field(..., gt=0, description="Type list ID")
    value_code: str = Field(..., min_length=1, max_length=50, description="Value code")
    value_label: str = Field(..., min_length=1, max_length=100, description="Value label")
    description: Optional[str] = Field(None, description="Value description")
    display_order: int = Field(default=0, description="Display order")
    is_default: bool = Field(default=False, description="Is default value")
    is_active: bool = Field(default=True, description="Is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata JSON (color, icon, etc.)")

    @field_validator('value_code')
    @classmethod
    def validate_value_code(cls, v):
        """Ensure value_code is uppercase and alphanumeric with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('value_code must be alphanumeric with underscores')
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "type_list_id": 1,
                "value_code": "CRITICAL",
                "value_label": "Critical",
                "description": "Critical severity - immediate action required",
                "display_order": 1,
                "is_default": False,
                "is_active": True,
                "metadata": {
                    "color": "#FF0000",
                    "icon": "alert-triangle",
                    "severity": "high"
                }
            }
        }


class TypeListValueResponse(BaseModel):
    """DTO for type list value response"""
    id: int
    organization_id: int
    type_list_id: int
    value_code: str
    value_label: str
    description: Optional[str] = None
    display_order: int
    is_default: bool
    is_active: bool
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "type_list_id": 1,
                "value_code": "CRITICAL",
                "value_label": "Critical",
                "description": "Critical severity - immediate action required",
                "display_order": 1,
                "is_default": False,
                "is_active": True,
                "metadata": {"color": "#FF0000", "icon": "alert-triangle"},
                "created_at": "2025-11-09T10:00:00Z",
                "updated_at": None
            }
        }


# ========== Entity Enrichment DTOs ==========

class EntityWithCustomFieldsResponse(BaseModel):
    """
    Mixin for enriching entity responses with custom field values.

    Usage:
        class MaterialWithCustomFieldsResponse(MaterialResponse, EntityWithCustomFieldsResponse):
            pass
    """
    custom_fields: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Custom field values keyed by field_code"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "custom_fields": {
                    "shelf_life_days": 45,
                    "storage_location": "A-12-3",
                    "hazmat_classification": "Class 3"
                }
            }
        }


# Update forward references for nested models
TypeListResponse.model_rebuild()
