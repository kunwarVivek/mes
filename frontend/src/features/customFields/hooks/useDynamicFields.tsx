import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { customFieldsService } from '@/services/customFields.service';
import type { CustomField, EntityType, FieldValuesBulkSet } from '@/types/customFields';
import { useState, useCallback } from 'react';

/**
 * Dynamic Fields Hook
 *
 * Provides custom fields for an entity type and handles value persistence.
 * Use this to inject custom fields into any form.
 *
 * @example
 * ```tsx
 * const { fields, values, setValue, saveValues, isLoading } = useDynamicFields('material', materialId);
 *
 * <form>
 *   {fields.map(field => (
 *     <DynamicFieldInput
 *       key={field.id}
 *       field={field}
 *       value={values[field.field_code]}
 *       onChange={value => setValue(field.field_code, value)}
 *     />
 *   ))}
 * </form>
 * ```
 */
export function useDynamicFields(entityType: EntityType, entityId?: number) {
  const queryClient = useQueryClient();
  const [localValues, setLocalValues] = useState<Record<string, any>>({});

  // Fetch custom field definitions for entity type
  const {
    data: fields = [],
    isLoading: isLoadingFields,
    error: fieldsError,
  } = useQuery<CustomField[]>({
    queryKey: ['customFields', entityType],
    queryFn: () => customFieldsService.getFieldsByEntityType(entityType),
  });

  // Fetch existing values (if entity already exists)
  const {
    data: existingValues = [],
    isLoading: isLoadingValues,
    error: valuesError,
  } = useQuery({
    queryKey: ['customFieldValues', entityType, entityId],
    queryFn: () => customFieldsService.getFieldValues(entityType, entityId!),
    enabled: !!entityId,
  });

  // Build values map
  const values: Record<string, any> = {};
  fields.forEach(field => {
    const existingValue = existingValues.find(v => v.custom_field_id === field.id);
    values[field.field_code] = localValues[field.field_code] ?? existingValue?.value ?? field.default_value ?? null;
  });

  // Set value function
  const setValue = useCallback((fieldCode: string, value: any) => {
    setLocalValues(prev => ({ ...prev, [fieldCode]: value }));
  }, []);

  // Set multiple values
  const setValues = useCallback((newValues: Record<string, any>) => {
    setLocalValues(prev => ({ ...prev, ...newValues }));
  }, []);

  // Mutation to save values
  const saveMutation = useMutation({
    mutationFn: (data: FieldValuesBulkSet) => customFieldsService.setFieldValuesBulk(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customFieldValues', entityType, entityId] });
      setLocalValues({});
    },
  });

  // Save values function
  const saveValues = useCallback(
    async (targetEntityId: number) => {
      if (!targetEntityId) {
        throw new Error('Entity ID is required to save custom field values');
      }

      const valuesToSave: Record<string, any> = {};
      fields.forEach(field => {
        const value = values[field.field_code];
        if (value !== null && value !== undefined && value !== '') {
          valuesToSave[field.field_code] = value;
        }
      });

      await saveMutation.mutateAsync({
        entity_type: entityType,
        entity_id: targetEntityId,
        values: valuesToSave,
      });
    },
    [fields, values, entityType, saveMutation]
  );

  // Validate all fields
  const validate = useCallback((): { isValid: boolean; errors: Record<string, string> } => {
    const errors: Record<string, string> = {};

    fields.forEach(field => {
      const value = values[field.field_code];
      const validation = customFieldsService.validateValue(field, value);
      if (!validation.isValid && validation.error) {
        errors[field.field_code] = validation.error;
      }
    });

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
    };
  }, [fields, values]);

  return {
    fields,
    values,
    setValue,
    setValues,
    saveValues,
    validate,
    isLoading: isLoadingFields || isLoadingValues,
    isSaving: saveMutation.isPending,
    error: fieldsError || valuesError,
  };
}

export default useDynamicFields;
