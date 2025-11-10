"""
Custom Field Service - Business logic for Configuration Engine
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.custom_field import CustomField, FieldValue, TypeList, TypeListValue
from app.infrastructure.repositories.custom_field_repository import (
    CustomFieldRepository,
    FieldValueRepository,
    TypeListRepository,
    TypeListValueRepository,
)
from app.application.dtos.custom_field_dto import (
    CustomFieldCreateDTO,
    CustomFieldUpdateDTO,
    FieldValueSetDTO,
    FieldValuesBulkSetDTO,
    TypeListCreateDTO,
    TypeListUpdateDTO,
    TypeListValueCreateDTO,
)


class CustomFieldService:
    """Service for Custom Fields and Configuration Engine operations"""

    def __init__(self, db: Session):
        self.db = db
        self.field_repo = CustomFieldRepository(db)
        self.value_repo = FieldValueRepository(db)
        self.type_list_repo = TypeListRepository(db)
        self.type_list_value_repo = TypeListValueRepository(db)

    # ========== Custom Field Management ==========

    def create_custom_field(self, dto: CustomFieldCreateDTO, created_by: Optional[int] = None) -> CustomField:
        """
        Create a new custom field.

        Validates that field_code is unique within entity_type + organization.
        """
        # Check if field code already exists for this entity type
        existing = self.field_repo.get_by_code(dto.organization_id, dto.entity_type, dto.field_code)
        if existing:
            raise ValueError(
                f"Custom field with code '{dto.field_code}' already exists for entity type '{dto.entity_type}'"
            )

        # Validate options for select/multiselect fields
        if dto.field_type in ('select', 'multiselect'):
            if not dto.options or len(dto.options) == 0:
                raise ValueError(f"Field type '{dto.field_type}' requires options to be specified")

        return self.field_repo.create(dto, created_by)

    def get_custom_field(self, field_id: int) -> Optional[CustomField]:
        """Get custom field by ID"""
        return self.field_repo.get_by_id(field_id)

    def list_custom_fields(self, organization_id: int, entity_type: str,
                          include_inactive: bool = False,
                          skip: int = 0, limit: int = 100) -> List[CustomField]:
        """List all custom fields for an entity type"""
        return self.field_repo.list_by_entity_type(
            organization_id, entity_type, include_inactive, skip, limit
        )

    def list_all_custom_fields(self, organization_id: int, entity_type: Optional[str] = None,
                              skip: int = 0, limit: int = 100) -> List[CustomField]:
        """List all custom fields, optionally filtered by entity type"""
        return self.field_repo.list_all(organization_id, entity_type, skip, limit)

    def update_custom_field(self, field_id: int, dto: CustomFieldUpdateDTO) -> Optional[CustomField]:
        """Update custom field"""
        field = self.field_repo.get_by_id(field_id)
        if not field:
            return None

        # Validate options if field type is select/multiselect
        if dto.options is not None:
            if field.field_type in ('select', 'multiselect') and len(dto.options) == 0:
                raise ValueError(f"Field type '{field.field_type}' requires at least one option")

        return self.field_repo.update(field_id, dto)

    def delete_custom_field(self, field_id: int) -> bool:
        """
        Delete custom field.

        Note: This will cascade delete all field values for this field.
        """
        field = self.field_repo.get_by_id(field_id)
        if not field:
            return False

        # You might want to add validation here to check if field is in use
        # and prevent deletion, or just allow cascade delete

        return self.field_repo.delete(field_id)

    # ========== Field Value Management ==========

    def set_field_value(self, organization_id: int, custom_field_id: int,
                       entity_type: str, entity_id: int, value: Any) -> FieldValue:
        """
        Set a field value for an entity instance.

        Validates the value against the field's validation rules.
        """
        # Get the custom field
        field = self.field_repo.get_by_id(custom_field_id)
        if not field:
            raise ValueError(f"Custom field {custom_field_id} not found")

        # Validate entity type matches
        if field.entity_type != entity_type:
            raise ValueError(
                f"Field '{field.field_code}' is for entity type '{field.entity_type}', "
                f"not '{entity_type}'"
            )

        # Validate the value using the field's validation method
        is_valid, error_message = field.validate_value(value)
        if not is_valid:
            raise ValueError(f"Validation failed: {error_message}")

        # Set the value
        return self.value_repo.set_value(
            organization_id=organization_id,
            custom_field_id=custom_field_id,
            entity_type=entity_type,
            entity_id=entity_id,
            value=value
        )

    def bulk_set_field_values(self, organization_id: int, dto: FieldValuesBulkSetDTO) -> List[FieldValue]:
        """
        Set multiple field values for an entity at once.

        Validates all values before setting any.
        """
        # Validate all values first
        fields_to_set = []
        for fv_dto in dto.field_values:
            field = self.field_repo.get_by_id(fv_dto.custom_field_id)
            if not field:
                raise ValueError(f"Custom field {fv_dto.custom_field_id} not found")

            # Validate entity type matches
            if field.entity_type != dto.entity_type:
                raise ValueError(
                    f"Field '{field.field_code}' is for entity type '{field.entity_type}', "
                    f"not '{dto.entity_type}'"
                )

            # Validate the value
            is_valid, error_message = field.validate_value(fv_dto.value)
            if not is_valid:
                raise ValueError(f"Validation failed for '{field.field_code}': {error_message}")

            fields_to_set.append((field, fv_dto))

        # All validations passed, now set the values
        return self.value_repo.bulk_set_values(
            organization_id=organization_id,
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            field_values=dto.field_values
        )

    def get_entity_field_values(self, entity_type: str, entity_id: int) -> List[FieldValue]:
        """Get all custom field values for an entity"""
        return self.value_repo.get_entity_values(entity_type, entity_id)

    def get_entity_field_values_dict(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        """
        Get all custom field values for an entity as a dictionary.

        Returns:
            Dict keyed by field_code with values
        """
        return self.value_repo.get_entity_values_dict(entity_type, entity_id)

    def enrich_entity_with_custom_fields(self, entity_dict: Dict[str, Any],
                                        entity_type: str, entity_id: int) -> Dict[str, Any]:
        """
        Enrich an entity response dictionary with custom field values.

        Args:
            entity_dict: Entity response as dict
            entity_type: Type of entity (material, work_order, etc.)
            entity_id: Entity ID

        Returns:
            Entity dict with 'custom_fields' key added
        """
        custom_fields = self.get_entity_field_values_dict(entity_type, entity_id)
        entity_dict['custom_fields'] = custom_fields
        return entity_dict

    def enrich_entities_with_custom_fields(self, entities: List[Dict[str, Any]],
                                          entity_type: str) -> List[Dict[str, Any]]:
        """
        Enrich multiple entity responses with custom field values.

        More efficient than calling enrich_entity_with_custom_fields() multiple times.

        Args:
            entities: List of entity dicts (must have 'id' field)
            entity_type: Type of entities

        Returns:
            List of entity dicts with 'custom_fields' key added
        """
        # Get all entity IDs
        entity_ids = [e['id'] for e in entities if 'id' in e]

        if not entity_ids:
            return entities

        # Get all field values for these entities
        # (In a real implementation, you'd want to optimize this with a single query)
        entity_custom_fields = {}
        for entity_id in entity_ids:
            entity_custom_fields[entity_id] = self.get_entity_field_values_dict(entity_type, entity_id)

        # Add custom fields to each entity
        for entity in entities:
            entity_id = entity.get('id')
            if entity_id:
                entity['custom_fields'] = entity_custom_fields.get(entity_id, {})

        return entities

    # ========== Type List Management ==========

    def create_type_list(self, dto: TypeListCreateDTO, created_by: Optional[int] = None) -> TypeList:
        """Create a new type list"""
        # Check if list code already exists
        existing = self.type_list_repo.get_by_code(dto.organization_id, dto.list_code)
        if existing:
            raise ValueError(f"Type list with code '{dto.list_code}' already exists")

        return self.type_list_repo.create(dto, created_by)

    def get_type_list(self, type_list_id: int) -> Optional[TypeList]:
        """Get type list by ID"""
        return self.type_list_repo.get_by_id(type_list_id)

    def get_type_list_by_code(self, organization_id: int, list_code: str) -> Optional[TypeList]:
        """Get type list by code"""
        return self.type_list_repo.get_by_code(organization_id, list_code)

    def get_type_list_with_values(self, organization_id: int, list_code: str) -> Optional[TypeList]:
        """Get type list with all its values"""
        return self.type_list_repo.get_with_values(organization_id, list_code)

    def list_type_lists(self, organization_id: int, category: Optional[str] = None,
                       include_inactive: bool = False,
                       skip: int = 0, limit: int = 100) -> List[TypeList]:
        """List all type lists"""
        return self.type_list_repo.list_all(organization_id, category, include_inactive, skip, limit)

    def update_type_list(self, type_list_id: int, dto: TypeListUpdateDTO) -> Optional[TypeList]:
        """Update type list (cannot update system lists)"""
        try:
            return self.type_list_repo.update(type_list_id, dto)
        except ValueError as e:
            raise e

    def delete_type_list(self, type_list_id: int) -> bool:
        """Delete type list (cannot delete system lists)"""
        type_list = self.type_list_repo.get_by_id(type_list_id)
        if not type_list:
            return False

        # Check if type list is used in any custom fields
        # (In a real implementation, you'd want to add this check)

        try:
            return self.type_list_repo.delete(type_list_id)
        except ValueError as e:
            raise e

    # ========== Type List Value Management ==========

    def add_type_list_value(self, organization_id: int, dto: TypeListValueCreateDTO) -> TypeListValue:
        """Add a value to a type list"""
        # Check if type list exists
        type_list = self.type_list_repo.get_by_id(dto.type_list_id)
        if not type_list:
            raise ValueError(f"Type list {dto.type_list_id} not found")

        # Check if value code already exists in this list
        existing = self.type_list_value_repo.get_by_code(dto.type_list_id, dto.value_code)
        if existing:
            raise ValueError(
                f"Value with code '{dto.value_code}' already exists in type list '{type_list.list_code}'"
            )

        # If this is set as default, unset any existing default
        if dto.is_default:
            current_default = self.type_list_value_repo.get_default_value(dto.type_list_id)
            if current_default:
                self.type_list_value_repo.update(current_default.id, {'is_default': False})

        return self.type_list_value_repo.create(organization_id, dto)

    def get_type_list_values(self, type_list_id: int,
                            include_inactive: bool = False) -> List[TypeListValue]:
        """Get all values for a type list"""
        return self.type_list_value_repo.list_by_type_list(type_list_id, include_inactive)

    def update_type_list_value(self, value_id: int, updates: Dict[str, Any]) -> Optional[TypeListValue]:
        """Update type list value"""
        # If setting as default, unset any existing default
        if updates.get('is_default') == True:
            value = self.type_list_value_repo.get_by_id(value_id)
            if value:
                current_default = self.type_list_value_repo.get_default_value(value.type_list_id)
                if current_default and current_default.id != value_id:
                    self.type_list_value_repo.update(current_default.id, {'is_default': False})

        return self.type_list_value_repo.update(value_id, updates)

    def delete_type_list_value(self, value_id: int) -> bool:
        """Delete type list value"""
        # You might want to add validation to check if value is in use
        return self.type_list_value_repo.delete(value_id)

    # ========== Validation Helpers ==========

    def validate_field_value(self, custom_field_id: int, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against a field's validation rules.

        Returns: (is_valid, error_message)
        """
        field = self.field_repo.get_by_id(custom_field_id)
        if not field:
            return False, f"Custom field {custom_field_id} not found"

        return field.validate_value(value)

    def get_field_schema(self, organization_id: int, entity_type: str) -> Dict[str, Any]:
        """
        Get the complete custom field schema for an entity type.

        Returns a JSON schema-like structure describing all custom fields.
        Useful for frontend form generation.
        """
        fields = self.field_repo.list_by_entity_type(organization_id, entity_type, include_inactive=False)

        schema = {
            "entity_type": entity_type,
            "fields": []
        }

        for field in fields:
            field_schema = {
                "id": field.id,
                "field_code": field.field_code,
                "field_label": field.field_label,
                "field_type": field.field_type,
                "description": field.description,
                "is_required": field.is_required,
                "default_value": field.default_value,
                "display_order": field.display_order,
                "validation_rules": field.validation_rules,
                "options": field.options,
                "ui_config": field.ui_config,
            }
            schema["fields"].append(field_schema)

        return schema
