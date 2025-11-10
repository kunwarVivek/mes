"""
Repository for Custom Fields Configuration Engine
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.models.custom_field import CustomField, FieldValue, TypeList, TypeListValue
from app.application.dtos.custom_field_dto import (
    CustomFieldCreateDTO,
    CustomFieldUpdateDTO,
    FieldValueSetDTO,
    TypeListCreateDTO,
    TypeListUpdateDTO,
    TypeListValueCreateDTO,
)


class CustomFieldRepository:
    """Repository for CustomField operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: CustomFieldCreateDTO, created_by: Optional[int] = None) -> CustomField:
        """Create a new custom field"""
        field = CustomField(
            organization_id=dto.organization_id,
            entity_type=dto.entity_type,
            field_name=dto.field_name,
            field_code=dto.field_code,
            field_label=dto.field_label,
            field_type=dto.field_type,
            description=dto.description,
            default_value=dto.default_value,
            is_required=dto.is_required,
            is_active=dto.is_active,
            display_order=dto.display_order,
            validation_rules=dto.validation_rules,
            options=dto.options,
            ui_config=dto.ui_config,
            created_by=created_by,
        )
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return field

    def get_by_id(self, field_id: int) -> Optional[CustomField]:
        """Get custom field by ID"""
        return self.db.query(CustomField).filter(CustomField.id == field_id).first()

    def get_by_code(self, organization_id: int, entity_type: str, field_code: str) -> Optional[CustomField]:
        """Get custom field by code within an organization and entity type"""
        return self.db.query(CustomField).filter(
            and_(
                CustomField.organization_id == organization_id,
                CustomField.entity_type == entity_type,
                CustomField.field_code == field_code
            )
        ).first()

    def list_by_entity_type(self, organization_id: int, entity_type: str,
                           include_inactive: bool = False,
                           skip: int = 0, limit: int = 100) -> List[CustomField]:
        """List all custom fields for an entity type"""
        query = self.db.query(CustomField).filter(
            and_(
                CustomField.organization_id == organization_id,
                CustomField.entity_type == entity_type
            )
        )

        if not include_inactive:
            query = query.filter(CustomField.is_active == True)

        return query.order_by(CustomField.display_order, CustomField.field_name).offset(skip).limit(limit).all()

    def list_all(self, organization_id: int, entity_type: Optional[str] = None,
                skip: int = 0, limit: int = 100) -> List[CustomField]:
        """List all custom fields, optionally filtered by entity type"""
        query = self.db.query(CustomField).filter(CustomField.organization_id == organization_id)

        if entity_type:
            query = query.filter(CustomField.entity_type == entity_type)

        return query.order_by(CustomField.entity_type, CustomField.display_order).offset(skip).limit(limit).all()

    def update(self, field_id: int, dto: CustomFieldUpdateDTO) -> Optional[CustomField]:
        """Update custom field"""
        field = self.get_by_id(field_id)
        if not field:
            return None

        # Update only provided fields
        if dto.field_name is not None:
            field.field_name = dto.field_name
        if dto.field_label is not None:
            field.field_label = dto.field_label
        if dto.description is not None:
            field.description = dto.description
        if dto.default_value is not None:
            field.default_value = dto.default_value
        if dto.is_required is not None:
            field.is_required = dto.is_required
        if dto.is_active is not None:
            field.is_active = dto.is_active
        if dto.display_order is not None:
            field.display_order = dto.display_order
        if dto.validation_rules is not None:
            field.validation_rules = dto.validation_rules
        if dto.options is not None:
            field.options = dto.options
        if dto.ui_config is not None:
            field.ui_config = dto.ui_config

        self.db.commit()
        self.db.refresh(field)
        return field

    def delete(self, field_id: int) -> bool:
        """Delete custom field (cascades to field_values)"""
        field = self.get_by_id(field_id)
        if not field:
            return False

        self.db.delete(field)
        self.db.commit()
        return True


class FieldValueRepository:
    """Repository for FieldValue operations"""

    def __init__(self, db: Session):
        self.db = db

    def set_value(self, organization_id: int, custom_field_id: int,
                 entity_type: str, entity_id: int, value: Any) -> FieldValue:
        """
        Set a field value for an entity.
        Creates new if doesn't exist, updates if exists.
        """
        # Check if value already exists
        existing = self.db.query(FieldValue).filter(
            and_(
                FieldValue.custom_field_id == custom_field_id,
                FieldValue.entity_id == entity_id
            )
        ).first()

        if existing:
            # Update existing value
            existing.value = value
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new value
            field_value = FieldValue(
                organization_id=organization_id,
                custom_field_id=custom_field_id,
                entity_type=entity_type,
                entity_id=entity_id,
                value=value,
            )
            self.db.add(field_value)
            self.db.commit()
            self.db.refresh(field_value)
            return field_value

    def get_value(self, custom_field_id: int, entity_id: int) -> Optional[FieldValue]:
        """Get a specific field value"""
        return self.db.query(FieldValue).filter(
            and_(
                FieldValue.custom_field_id == custom_field_id,
                FieldValue.entity_id == entity_id
            )
        ).first()

    def get_entity_values(self, entity_type: str, entity_id: int) -> List[FieldValue]:
        """Get all custom field values for an entity instance"""
        return self.db.query(FieldValue).options(
            joinedload(FieldValue.custom_field)
        ).filter(
            and_(
                FieldValue.entity_type == entity_type,
                FieldValue.entity_id == entity_id
            )
        ).all()

    def get_entity_values_dict(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        """
        Get all custom field values for an entity as a dictionary.

        Returns:
            Dict keyed by field_code with values
        """
        field_values = self.get_entity_values(entity_type, entity_id)

        result = {}
        for fv in field_values:
            if fv.custom_field and fv.custom_field.is_active:
                result[fv.custom_field.field_code] = fv.value

        return result

    def bulk_set_values(self, organization_id: int, entity_type: str,
                       entity_id: int, field_values: List[FieldValueSetDTO]) -> List[FieldValue]:
        """
        Set multiple field values for an entity at once.

        This is more efficient than calling set_value() multiple times.
        """
        results = []
        for fv_dto in field_values:
            field_value = self.set_value(
                organization_id=organization_id,
                custom_field_id=fv_dto.custom_field_id,
                entity_type=entity_type,
                entity_id=entity_id,
                value=fv_dto.value
            )
            results.append(field_value)

        return results

    def delete_value(self, custom_field_id: int, entity_id: int) -> bool:
        """Delete a field value"""
        field_value = self.get_value(custom_field_id, entity_id)
        if not field_value:
            return False

        self.db.delete(field_value)
        self.db.commit()
        return True

    def delete_entity_values(self, entity_type: str, entity_id: int) -> int:
        """
        Delete all custom field values for an entity.

        Returns:
            Number of values deleted
        """
        count = self.db.query(FieldValue).filter(
            and_(
                FieldValue.entity_type == entity_type,
                FieldValue.entity_id == entity_id
            )
        ).delete()
        self.db.commit()
        return count


class TypeListRepository:
    """Repository for TypeList operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: TypeListCreateDTO, created_by: Optional[int] = None) -> TypeList:
        """Create a new type list"""
        type_list = TypeList(
            organization_id=dto.organization_id,
            list_name=dto.list_name,
            list_code=dto.list_code,
            description=dto.description,
            category=dto.category,
            is_system_list=False,  # User-created lists are never system lists
            is_active=True,
            allow_custom_values=dto.allow_custom_values,
            created_by=created_by,
        )
        self.db.add(type_list)
        self.db.commit()
        self.db.refresh(type_list)
        return type_list

    def get_by_id(self, type_list_id: int) -> Optional[TypeList]:
        """Get type list by ID"""
        return self.db.query(TypeList).filter(TypeList.id == type_list_id).first()

    def get_by_code(self, organization_id: int, list_code: str) -> Optional[TypeList]:
        """Get type list by code within an organization"""
        return self.db.query(TypeList).filter(
            and_(
                TypeList.organization_id == organization_id,
                TypeList.list_code == list_code
            )
        ).first()

    def get_with_values(self, organization_id: int, list_code: str) -> Optional[TypeList]:
        """Get type list with all its values"""
        return self.db.query(TypeList).options(
            joinedload(TypeList.values)
        ).filter(
            and_(
                TypeList.organization_id == organization_id,
                TypeList.list_code == list_code
            )
        ).first()

    def list_all(self, organization_id: int, category: Optional[str] = None,
                include_inactive: bool = False,
                skip: int = 0, limit: int = 100) -> List[TypeList]:
        """List all type lists"""
        query = self.db.query(TypeList).filter(TypeList.organization_id == organization_id)

        if category:
            query = query.filter(TypeList.category == category)

        if not include_inactive:
            query = query.filter(TypeList.is_active == True)

        return query.order_by(TypeList.category, TypeList.list_name).offset(skip).limit(limit).all()

    def update(self, type_list_id: int, dto: TypeListUpdateDTO) -> Optional[TypeList]:
        """Update type list (only for non-system lists)"""
        type_list = self.get_by_id(type_list_id)
        if not type_list:
            return None

        # Prevent updates to system lists
        if type_list.is_system_list:
            raise ValueError("Cannot modify system type lists")

        if dto.list_name is not None:
            type_list.list_name = dto.list_name
        if dto.description is not None:
            type_list.description = dto.description
        if dto.category is not None:
            type_list.category = dto.category
        if dto.is_active is not None:
            type_list.is_active = dto.is_active
        if dto.allow_custom_values is not None:
            type_list.allow_custom_values = dto.allow_custom_values

        self.db.commit()
        self.db.refresh(type_list)
        return type_list

    def delete(self, type_list_id: int) -> bool:
        """Delete type list (only for non-system lists)"""
        type_list = self.get_by_id(type_list_id)
        if not type_list:
            return False

        # Prevent deletion of system lists
        if type_list.is_system_list:
            raise ValueError("Cannot delete system type lists")

        self.db.delete(type_list)
        self.db.commit()
        return True


class TypeListValueRepository:
    """Repository for TypeListValue operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, organization_id: int, dto: TypeListValueCreateDTO) -> TypeListValue:
        """Create a new type list value"""
        value = TypeListValue(
            organization_id=organization_id,
            type_list_id=dto.type_list_id,
            value_code=dto.value_code,
            value_label=dto.value_label,
            description=dto.description,
            display_order=dto.display_order,
            is_default=dto.is_default,
            is_active=dto.is_active,
            metadata=dto.metadata,
        )
        self.db.add(value)
        self.db.commit()
        self.db.refresh(value)
        return value

    def get_by_id(self, value_id: int) -> Optional[TypeListValue]:
        """Get type list value by ID"""
        return self.db.query(TypeListValue).filter(TypeListValue.id == value_id).first()

    def get_by_code(self, type_list_id: int, value_code: str) -> Optional[TypeListValue]:
        """Get type list value by code within a type list"""
        return self.db.query(TypeListValue).filter(
            and_(
                TypeListValue.type_list_id == type_list_id,
                TypeListValue.value_code == value_code
            )
        ).first()

    def list_by_type_list(self, type_list_id: int,
                         include_inactive: bool = False) -> List[TypeListValue]:
        """List all values for a type list"""
        query = self.db.query(TypeListValue).filter(
            TypeListValue.type_list_id == type_list_id
        )

        if not include_inactive:
            query = query.filter(TypeListValue.is_active == True)

        return query.order_by(TypeListValue.display_order, TypeListValue.value_label).all()

    def update(self, value_id: int, updates: Dict[str, Any]) -> Optional[TypeListValue]:
        """Update type list value"""
        value = self.get_by_id(value_id)
        if not value:
            return None

        for key, val in updates.items():
            if hasattr(value, key):
                setattr(value, key, val)

        self.db.commit()
        self.db.refresh(value)
        return value

    def delete(self, value_id: int) -> bool:
        """Delete type list value"""
        value = self.get_by_id(value_id)
        if not value:
            return False

        self.db.delete(value)
        self.db.commit()
        return True

    def get_default_value(self, type_list_id: int) -> Optional[TypeListValue]:
        """Get the default value for a type list"""
        return self.db.query(TypeListValue).filter(
            and_(
                TypeListValue.type_list_id == type_list_id,
                TypeListValue.is_default == True,
                TypeListValue.is_active == True
            )
        ).first()
