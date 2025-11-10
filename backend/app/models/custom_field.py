"""
Custom Fields and Type Lists models for Configuration Engine

Enables self-service configuration of custom fields per entity type
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CustomField(Base):
    """
    Custom field definition per entity type.

    Allows organizations to add custom fields to any entity
    (materials, work_orders, projects, NCRs, etc.) without code changes.

    This is the core of the Configuration Engine.
    """
    __tablename__ = 'custom_fields'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Entity configuration
    entity_type = Column(String(50), nullable=False)  # material, work_order, ncr, project, etc.
    field_name = Column(String(100), nullable=False)
    field_code = Column(String(50), nullable=False)  # Internal identifier (snake_case)
    field_label = Column(String(100), nullable=False)  # Display label

    # Field type: text, number, date, datetime, select, multiselect, boolean, file, textarea, email, url, phone
    field_type = Column(String(50), nullable=False)

    description = Column(Text, nullable=True)
    default_value = Column(Text, nullable=True)
    is_required = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)

    # JSONB validation rules
    # {
    #   "min_length": 5,
    #   "max_length": 100,
    #   "pattern": "^[A-Z0-9-]+$",
    #   "min_value": 0,
    #   "max_value": 100,
    #   "allowed_file_types": ["pdf", "jpg", "png"],
    #   "date_range": {"min": "2020-01-01", "max": "2030-12-31"}
    # }
    validation_rules = Column(JSONB, nullable=True)

    # JSONB options for select/multiselect fields
    # [
    #   {"value": "option1", "label": "Option 1"},
    #   {"value": "option2", "label": "Option 2", "disabled": false}
    # ]
    options = Column(JSONB, nullable=True)

    # JSONB UI configuration
    # {
    #   "placeholder": "Enter value...",
    #   "help_text": "This field is for...",
    #   "icon": "calendar",
    #   "width": "full",
    #   "conditional_visibility": {"field": "status", "value": "APPROVED"}
    # }
    ui_config = Column(JSONB, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    field_values = relationship("FieldValue", back_populates="custom_field", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'entity_type', 'field_code',
                        name='uq_custom_field_code_per_entity'),
        Index('idx_custom_fields_org', 'organization_id'),
        Index('idx_custom_fields_entity', 'organization_id', 'entity_type'),
        Index('idx_custom_fields_active', 'organization_id', 'entity_type', 'is_active'),
    )

    def __repr__(self):
        return f"<CustomField(id={self.id}, entity='{self.entity_type}', code='{self.field_code}')>"

    def validate_value(self, value):
        """
        Validate a value against this field's validation rules.

        Returns: (is_valid, error_message)
        """
        if value is None:
            if self.is_required:
                return False, f"{self.field_label} is required"
            return True, None

        rules = self.validation_rules or {}

        # Text validation
        if self.field_type in ('text', 'textarea', 'email', 'url', 'phone'):
            if not isinstance(value, str):
                return False, f"{self.field_label} must be a string"

            if 'min_length' in rules and len(value) < rules['min_length']:
                return False, f"{self.field_label} must be at least {rules['min_length']} characters"

            if 'max_length' in rules and len(value) > rules['max_length']:
                return False, f"{self.field_label} must be at most {rules['max_length']} characters"

            if 'pattern' in rules:
                import re
                if not re.match(rules['pattern'], value):
                    return False, f"{self.field_label} format is invalid"

        # Number validation
        elif self.field_type == 'number':
            try:
                num_value = float(value)
            except (ValueError, TypeError):
                return False, f"{self.field_label} must be a number"

            if 'min_value' in rules and num_value < rules['min_value']:
                return False, f"{self.field_label} must be at least {rules['min_value']}"

            if 'max_value' in rules and num_value > rules['max_value']:
                return False, f"{self.field_label} must be at most {rules['max_value']}"

        # Boolean validation
        elif self.field_type == 'boolean':
            if not isinstance(value, bool):
                return False, f"{self.field_label} must be true or false"

        # Select/multiselect validation
        elif self.field_type in ('select', 'multiselect'):
            if not self.options:
                return False, "Field options not configured"

            valid_values = {opt['value'] for opt in self.options if isinstance(opt, dict)}

            if self.field_type == 'select':
                if value not in valid_values:
                    return False, f"{self.field_label} must be one of: {', '.join(valid_values)}"
            else:  # multiselect
                if not isinstance(value, list):
                    return False, f"{self.field_label} must be a list"
                for v in value:
                    if v not in valid_values:
                        return False, f"Invalid value '{v}' in {self.field_label}"

        return True, None


class FieldValue(Base):
    """
    Storage for custom field values.

    Uses JSONB for flexible value storage (string, number, array, object).
    """
    __tablename__ = 'field_values'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    custom_field_id = Column(Integer, ForeignKey('custom_fields.id', ondelete='CASCADE'), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)

    # JSONB value storage
    # Can store: string, number, boolean, array, object
    value = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    custom_field = relationship("CustomField", back_populates="field_values")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('custom_field_id', 'entity_id', name='uq_field_value_per_entity'),
        Index('idx_field_values_org', 'organization_id'),
        Index('idx_field_values_entity', 'entity_type', 'entity_id'),
        Index('idx_field_values_field', 'custom_field_id'),
        Index('idx_field_values_value_gin', 'value', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<FieldValue(field_id={self.custom_field_id}, entity={self.entity_type}:{self.entity_id})>"


class TypeList(Base):
    """
    Configurable type taxonomies.

    Examples: NCR severity levels, defect types, work order priorities, etc.
    Allows organizations to configure their own type systems.
    """
    __tablename__ = 'type_lists'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    list_name = Column(String(100), nullable=False)
    list_code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # Group related lists (quality, production, etc.)

    is_system_list = Column(Boolean, nullable=False, default=False)  # System lists can't be deleted
    is_active = Column(Boolean, nullable=False, default=True)
    allow_custom_values = Column(Boolean, nullable=False, default=False)  # Allow users to add values

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    values = relationship("TypeListValue", back_populates="type_list", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'list_code', name='uq_type_list_code_per_org'),
        Index('idx_type_lists_org', 'organization_id'),
        Index('idx_type_lists_code', 'organization_id', 'list_code'),
        Index('idx_type_lists_category', 'organization_id', 'category'),
    )

    def __repr__(self):
        return f"<TypeList(id={self.id}, code='{self.list_code}', name='{self.list_name}')>"


class TypeListValue(Base):
    """
    Values for type lists.

    Each value has a code, label, and optional metadata (color, icon, etc.)
    """
    __tablename__ = 'type_list_values'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    type_list_id = Column(Integer, ForeignKey('type_lists.id', ondelete='CASCADE'), nullable=False)

    value_code = Column(String(50), nullable=False)
    value_label = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # JSONB metadata
    # {
    #   "color": "#FF0000",
    #   "icon": "alert-triangle",
    #   "severity": "high",
    #   "requires_approval": true,
    #   "workflow_id": 5
    # }
    metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    type_list = relationship("TypeList", back_populates="values")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('type_list_id', 'value_code', name='uq_type_value_code_per_list'),
        Index('idx_type_list_values_org', 'organization_id'),
        Index('idx_type_list_values_list', 'type_list_id'),
        Index('idx_type_list_values_active', 'type_list_id', 'is_active'),
    )

    def __repr__(self):
        return f"<TypeListValue(id={self.id}, code='{self.value_code}', label='{self.value_label}')>"
