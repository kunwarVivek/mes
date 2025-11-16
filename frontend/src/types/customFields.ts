// Custom Fields Types and Interfaces
export interface CustomField {
  id: number;
  organization_id: number;
  entity_type: EntityType;
  field_name: string;
  field_code: string;
  field_label: string;
  field_type: FieldType;
  description?: string;
  default_value?: string;
  is_required: boolean;
  is_active: boolean;
  display_order: number;
  validation_rules?: ValidationRules;
  options?: FieldOption[];
  ui_config?: UIConfig;
  created_at: string;
  updated_at?: string;
  created_by?: number;
}

export type EntityType =
  | 'material'
  | 'work_order'
  | 'project'
  | 'ncr'
  | 'machine'
  | 'department'
  | 'plant'
  | 'organization'
  | 'maintenance'
  | 'production_log'
  | 'quality'
  | 'shift'
  | 'lane'
  | 'user'
  | 'bom';

export type FieldType =
  | 'text'
  | 'number'
  | 'date'
  | 'datetime'
  | 'select'
  | 'multiselect'
  | 'boolean'
  | 'file'
  | 'textarea'
  | 'email'
  | 'url'
  | 'phone';

export interface ValidationRules {
  min_length?: number;
  max_length?: number;
  pattern?: string;
  min_value?: number;
  max_value?: number;
  allowed_file_types?: string[];
  date_range?: {
    min?: string;
    max?: string;
  };
}

export interface FieldOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface UIConfig {
  placeholder?: string;
  help_text?: string;
  icon?: string;
  width?: 'full' | 'half' | 'third';
  conditional_visibility?: {
    field: string;
    value: any;
  };
}

export interface FieldValue {
  id: number;
  organization_id: number;
  custom_field_id: number;
  entity_type: EntityType;
  entity_id: number;
  value: any;
  created_at: string;
  updated_at?: string;
}

export interface CustomFieldCreate {
  organization_id: number;
  entity_type: EntityType;
  field_name: string;
  field_code: string;
  field_label: string;
  field_type: FieldType;
  description?: string;
  default_value?: string;
  is_required?: boolean;
  is_active?: boolean;
  display_order?: number;
  validation_rules?: ValidationRules;
  options?: FieldOption[];
  ui_config?: UIConfig;
}

export interface CustomFieldUpdate {
  field_name?: string;
  field_label?: string;
  description?: string;
  default_value?: string;
  is_required?: boolean;
  is_active?: boolean;
  display_order?: number;
  validation_rules?: ValidationRules;
  options?: FieldOption[];
  ui_config?: UIConfig;
}

export interface FieldValueSet {
  entity_id: number;
  field_code: string;
  value: any;
}

export interface FieldValuesBulkSet {
  entity_type: EntityType;
  entity_id: number;
  values: Record<string, any>;
}

export interface TypeList {
  id: number;
  organization_id: number;
  list_name: string;
  list_code: string;
  description?: string;
  category?: string;
  is_system_list: boolean;
  is_active: boolean;
  allow_custom_values: boolean;
  created_at: string;
  updated_at?: string;
  created_by?: number;
  values?: TypeListValue[];
}

export interface TypeListValue {
  id: number;
  organization_id: number;
  type_list_id: number;
  value_code: string;
  value_label: string;
  description?: string;
  display_order: number;
  is_default: boolean;
  is_active: boolean;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}
