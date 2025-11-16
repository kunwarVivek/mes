import apiClient from './api.client';
import type {
  CustomField,
  CustomFieldCreate,
  CustomFieldUpdate,
  FieldValue,
  FieldValueSet,
  FieldValuesBulkSet,
  EntityType,
} from '@/types/customFields';

/**
 * Custom Fields Service
 *
 * Manages custom field definitions and values for any entity type.
 * Enables self-service configuration without code changes.
 */
class CustomFieldsService {
  private baseUrl = '/api/v1/custom-fields';

  // ========== Custom Field Definition Management ==========

  /**
   * Get all custom fields for an entity type
   */
  async getFieldsByEntityType(entityType: EntityType): Promise<CustomField[]> {
    const response = await apiClient.get<CustomField[]>(
      `${this.baseUrl}/entity/${entityType}`
    );
    return response.data;
  }

  /**
   * Get custom field by ID
   */
  async getFieldById(fieldId: number): Promise<CustomField> {
    const response = await apiClient.get<CustomField>(`${this.baseUrl}/${fieldId}`);
    return response.data;
  }

  /**
   * Get all custom fields for organization
   */
  async getAllFields(): Promise<CustomField[]> {
    const response = await apiClient.get<CustomField[]>(this.baseUrl);
    return response.data;
  }

  /**
   * Create a new custom field
   */
  async createField(data: CustomFieldCreate): Promise<CustomField> {
    const response = await apiClient.post<CustomField>(this.baseUrl, data);
    return response.data;
  }

  /**
   * Update an existing custom field
   */
  async updateField(fieldId: number, data: CustomFieldUpdate): Promise<CustomField> {
    const response = await apiClient.put<CustomField>(`${this.baseUrl}/${fieldId}`, data);
    return response.data;
  }

  /**
   * Delete a custom field (soft delete - marks inactive)
   */
  async deleteField(fieldId: number): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${fieldId}`);
  }

  /**
   * Reorder custom fields (update display_order)
   */
  async reorderFields(
    entityType: EntityType,
    fieldOrders: Array<{ field_id: number; display_order: number }>
  ): Promise<void> {
    await apiClient.post(`${this.baseUrl}/reorder`, {
      entity_type: entityType,
      field_orders: fieldOrders,
    });
  }

  // ========== Field Value Management ==========

  /**
   * Get all custom field values for an entity
   */
  async getFieldValues(entityType: EntityType, entityId: number): Promise<FieldValue[]> {
    const response = await apiClient.get<FieldValue[]>(
      `${this.baseUrl}/values/${entityType}/${entityId}`
    );
    return response.data;
  }

  /**
   * Set a single field value
   */
  async setFieldValue(
    entityType: EntityType,
    data: FieldValueSet
  ): Promise<FieldValue> {
    const response = await apiClient.post<FieldValue>(
      `${this.baseUrl}/values/${entityType}`,
      data
    );
    return response.data;
  }

  /**
   * Set multiple field values at once (bulk operation)
   */
  async setFieldValuesBulk(data: FieldValuesBulkSet): Promise<FieldValue[]> {
    const response = await apiClient.post<FieldValue[]>(
      `${this.baseUrl}/values/bulk`,
      data
    );
    return response.data;
  }

  /**
   * Get custom field values with definitions (joined query)
   * Returns values with their field definitions for easy rendering
   */
  async getFieldValuesWithDefinitions(
    entityType: EntityType,
    entityId: number
  ): Promise<Array<{ field: CustomField; value: any }>> {
    const [fields, values] = await Promise.all([
      this.getFieldsByEntityType(entityType),
      this.getFieldValues(entityType, entityId),
    ]);

    const valueMap = new Map(values.map(v => [v.custom_field_id, v.value]));

    return fields.map(field => ({
      field,
      value: valueMap.get(field.id) ?? field.default_value ?? null,
    }));
  }

  /**
   * Validate field value against validation rules
   */
  validateValue(field: CustomField, value: any): { isValid: boolean; error?: string } {
    if (value === null || value === undefined || value === '') {
      if (field.is_required) {
        return { isValid: false, error: `${field.field_label} is required` };
      }
      return { isValid: true };
    }

    const rules = field.validation_rules || {};

    // Text validation
    if (['text', 'textarea', 'email', 'url', 'phone'].includes(field.field_type)) {
      if (typeof value !== 'string') {
        return { isValid: false, error: `${field.field_label} must be a string` };
      }

      if (rules.min_length && value.length < rules.min_length) {
        return {
          isValid: false,
          error: `${field.field_label} must be at least ${rules.min_length} characters`,
        };
      }

      if (rules.max_length && value.length > rules.max_length) {
        return {
          isValid: false,
          error: `${field.field_label} must be at most ${rules.max_length} characters`,
        };
      }

      if (rules.pattern) {
        const regex = new RegExp(rules.pattern);
        if (!regex.test(value)) {
          return { isValid: false, error: `${field.field_label} format is invalid` };
        }
      }

      // Email validation
      if (field.field_type === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          return { isValid: false, error: 'Invalid email format' };
        }
      }

      // URL validation
      if (field.field_type === 'url') {
        try {
          new URL(value);
        } catch {
          return { isValid: false, error: 'Invalid URL format' };
        }
      }
    }

    // Number validation
    if (field.field_type === 'number') {
      const numValue = Number(value);
      if (isNaN(numValue)) {
        return { isValid: false, error: `${field.field_label} must be a number` };
      }

      if (rules.min_value !== undefined && numValue < rules.min_value) {
        return {
          isValid: false,
          error: `${field.field_label} must be at least ${rules.min_value}`,
        };
      }

      if (rules.max_value !== undefined && numValue > rules.max_value) {
        return {
          isValid: false,
          error: `${field.field_label} must be at most ${rules.max_value}`,
        };
      }
    }

    // Boolean validation
    if (field.field_type === 'boolean') {
      if (typeof value !== 'boolean') {
        return { isValid: false, error: `${field.field_label} must be true or false` };
      }
    }

    // Select/Multiselect validation
    if (['select', 'multiselect'].includes(field.field_type)) {
      if (!field.options || field.options.length === 0) {
        return { isValid: false, error: 'Field options not configured' };
      }

      const validValues = new Set(field.options.map(opt => opt.value));

      if (field.field_type === 'select') {
        if (!validValues.has(value)) {
          return {
            isValid: false,
            error: `${field.field_label} must be one of: ${field.options
              .map(o => o.label)
              .join(', ')}`,
          };
        }
      } else {
        // multiselect
        if (!Array.isArray(value)) {
          return { isValid: false, error: `${field.field_label} must be a list` };
        }
        for (const v of value) {
          if (!validValues.has(v)) {
            return { isValid: false, error: `Invalid value '${v}' in ${field.field_label}` };
          }
        }
      }
    }

    // Date validation
    if (['date', 'datetime'].includes(field.field_type)) {
      const date = new Date(value);
      if (isNaN(date.getTime())) {
        return { isValid: false, error: 'Invalid date format' };
      }

      if (rules.date_range) {
        if (rules.date_range.min && date < new Date(rules.date_range.min)) {
          return {
            isValid: false,
            error: `Date must be after ${rules.date_range.min}`,
          };
        }
        if (rules.date_range.max && date > new Date(rules.date_range.max)) {
          return {
            isValid: false,
            error: `Date must be before ${rules.date_range.max}`,
          };
        }
      }
    }

    return { isValid: true };
  }
}

export const customFieldsService = new CustomFieldsService();
export default customFieldsService;
