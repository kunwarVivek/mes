import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { customFieldsService } from '@/services/customFields.service';
import type {
  CustomField,
  CustomFieldCreate,
  CustomFieldUpdate,
  EntityType,
  FieldType,
  FieldOption,
} from '@/types/customFields';
import { X, Plus, Trash2 } from 'lucide-react';

interface CustomFieldFormProps {
  field?: CustomField;
  onClose: () => void;
  onSuccess?: () => void;
}

/**
 * Custom Field Create/Edit Form
 *
 * Comprehensive form for defining custom field configuration
 */
export const CustomFieldForm: React.FC<CustomFieldFormProps> = ({
  field,
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const isEditMode = !!field;

  // Form state
  const [formData, setFormData] = useState({
    organization_id: field?.organization_id || 1,
    entity_type: field?.entity_type || ('material' as EntityType),
    field_name: field?.field_name || '',
    field_code: field?.field_code || '',
    field_label: field?.field_label || '',
    field_type: field?.field_type || ('text' as FieldType),
    description: field?.description || '',
    default_value: field?.default_value || '',
    is_required: field?.is_required || false,
    is_active: field?.is_active !== undefined ? field.is_active : true,
    display_order: field?.display_order || 0,
  });

  const [validationRules, setValidationRules] = useState({
    min_length: field?.validation_rules?.min_length || '',
    max_length: field?.validation_rules?.max_length || '',
    pattern: field?.validation_rules?.pattern || '',
    min_value: field?.validation_rules?.min_value || '',
    max_value: field?.validation_rules?.max_value || '',
  });

  const [options, setOptions] = useState<FieldOption[]>(
    field?.options || [{ value: '', label: '' }]
  );

  const [uiConfig, setUiConfig] = useState({
    placeholder: field?.ui_config?.placeholder || '',
    help_text: field?.ui_config?.help_text || '',
    width: field?.ui_config?.width || 'full',
  });

  // Auto-generate field_code from field_name
  useEffect(() => {
    if (!isEditMode && formData.field_name) {
      const code = formData.field_name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/^_|_$/g, '');
      setFormData(prev => ({ ...prev, field_code: code }));
    }
  }, [formData.field_name, isEditMode]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: CustomFieldCreate) => customFieldsService.createField(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customFields'] });
      onSuccess?.();
      onClose();
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ fieldId, data }: { fieldId: number; data: CustomFieldUpdate }) =>
      customFieldsService.updateField(fieldId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customFields'] });
      onSuccess?.();
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Build validation rules object
    const validationRulesObj: any = {};
    if (validationRules.min_length) validationRulesObj.min_length = Number(validationRules.min_length);
    if (validationRules.max_length) validationRulesObj.max_length = Number(validationRules.max_length);
    if (validationRules.pattern) validationRulesObj.pattern = validationRules.pattern;
    if (validationRules.min_value) validationRulesObj.min_value = Number(validationRules.min_value);
    if (validationRules.max_value) validationRulesObj.max_value = Number(validationRules.max_value);

    // Build ui_config object
    const uiConfigObj: any = {};
    if (uiConfig.placeholder) uiConfigObj.placeholder = uiConfig.placeholder;
    if (uiConfig.help_text) uiConfigObj.help_text = uiConfig.help_text;
    if (uiConfig.width) uiConfigObj.width = uiConfig.width;

    // Build options array (only for select/multiselect)
    const optionsArr =
      formData.field_type === 'select' || formData.field_type === 'multiselect'
        ? options.filter(opt => opt.value && opt.label)
        : undefined;

    if (isEditMode) {
      const updateData: CustomFieldUpdate = {
        field_name: formData.field_name,
        field_label: formData.field_label,
        description: formData.description || undefined,
        default_value: formData.default_value || undefined,
        is_required: formData.is_required,
        is_active: formData.is_active,
        display_order: formData.display_order,
        validation_rules: Object.keys(validationRulesObj).length > 0 ? validationRulesObj : undefined,
        options: optionsArr,
        ui_config: Object.keys(uiConfigObj).length > 0 ? uiConfigObj : undefined,
      };
      updateMutation.mutate({ fieldId: field!.id, data: updateData });
    } else {
      const createData: CustomFieldCreate = {
        ...formData,
        validation_rules: Object.keys(validationRulesObj).length > 0 ? validationRulesObj : undefined,
        options: optionsArr,
        ui_config: Object.keys(uiConfigObj).length > 0 ? uiConfigObj : undefined,
      };
      createMutation.mutate(createData);
    }
  };

  const addOption = () => {
    setOptions([...options, { value: '', label: '' }]);
  };

  const removeOption = (index: number) => {
    setOptions(options.filter((_, i) => i !== index));
  };

  const updateOption = (index: number, field: 'value' | 'label', value: string) => {
    const newOptions = [...options];
    newOptions[index][field] = value;
    setOptions(newOptions);
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <h2 className="text-xl font-semibold text-gray-900">
            {isEditMode ? 'Edit Custom Field' : 'Create Custom Field'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Entity Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.entity_type}
                  onChange={e => setFormData({ ...formData, entity_type: e.target.value as EntityType })}
                  disabled={isEditMode}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  required
                >
                  <option value="material">Material</option>
                  <option value="work_order">Work Order</option>
                  <option value="project">Project</option>
                  <option value="ncr">NCR</option>
                  <option value="machine">Machine</option>
                  <option value="quality">Quality</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="shift">Shift</option>
                  <option value="lane">Lane</option>
                  <option value="bom">BOM</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Field Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.field_type}
                  onChange={e => setFormData({ ...formData, field_type: e.target.value as FieldType })}
                  disabled={isEditMode}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  required
                >
                  <option value="text">Text</option>
                  <option value="textarea">Text Area</option>
                  <option value="number">Number</option>
                  <option value="email">Email</option>
                  <option value="url">URL</option>
                  <option value="phone">Phone</option>
                  <option value="date">Date</option>
                  <option value="datetime">Date & Time</option>
                  <option value="select">Select (Dropdown)</option>
                  <option value="multiselect">Multi-Select</option>
                  <option value="boolean">Boolean (Yes/No)</option>
                  <option value="file">File Upload</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Field Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.field_name}
                onChange={e => setFormData({ ...formData, field_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Shelf Life Days"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Field Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.field_code}
                  onChange={e => setFormData({ ...formData, field_code: e.target.value.toLowerCase() })}
                  disabled={isEditMode}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm disabled:bg-gray-100"
                  placeholder="shelf_life_days"
                  pattern="[a-z0-9_]+"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Lowercase, numbers, underscores only</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Field Label <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.field_label}
                  onChange={e => setFormData({ ...formData, field_label: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Shelf Life (Days)"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={e => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
                placeholder="Brief description of this field"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Default Value</label>
                <input
                  type="text"
                  value={formData.default_value}
                  onChange={e => setFormData({ ...formData, default_value: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Display Order</label>
                <input
                  type="number"
                  value={formData.display_order}
                  onChange={e => setFormData({ ...formData, display_order: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                />
              </div>

              <div className="space-y-2 pt-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_required}
                    onChange={e => setFormData({ ...formData, is_required: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Required</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Active</span>
                </label>
              </div>
            </div>
          </div>

          {/* Validation Rules */}
          {['text', 'textarea', 'number', 'email', 'url', 'phone'].includes(formData.field_type) && (
            <div className="space-y-4 border-t border-gray-200 pt-6">
              <h3 className="text-lg font-medium text-gray-900">Validation Rules</h3>

              {['text', 'textarea', 'email', 'url', 'phone'].includes(formData.field_type) && (
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Length
                    </label>
                    <input
                      type="number"
                      value={validationRules.min_length}
                      onChange={e => setValidationRules({ ...validationRules, min_length: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="0"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Length
                    </label>
                    <input
                      type="number"
                      value={validationRules.max_length}
                      onChange={e => setValidationRules({ ...validationRules, max_length: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="0"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Pattern (Regex)
                    </label>
                    <input
                      type="text"
                      value={validationRules.pattern}
                      onChange={e => setValidationRules({ ...validationRules, pattern: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      placeholder="^[A-Z0-9-]+$"
                    />
                  </div>
                </div>
              )}

              {formData.field_type === 'number' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Value
                    </label>
                    <input
                      type="number"
                      value={validationRules.min_value}
                      onChange={e => setValidationRules({ ...validationRules, min_value: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      step="any"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Value
                    </label>
                    <input
                      type="number"
                      value={validationRules.max_value}
                      onChange={e => setValidationRules({ ...validationRules, max_value: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      step="any"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Options for Select/Multiselect */}
          {(formData.field_type === 'select' || formData.field_type === 'multiselect') && (
            <div className="space-y-4 border-t border-gray-200 pt-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Options</h3>
                <button
                  type="button"
                  onClick={addOption}
                  className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                >
                  <Plus className="h-4 w-4" />
                  Add Option
                </button>
              </div>

              <div className="space-y-2">
                {options.map((option, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={option.value}
                      onChange={e => updateOption(index, 'value', e.target.value)}
                      placeholder="Value (stored in database)"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      required
                    />
                    <input
                      type="text"
                      value={option.label}
                      onChange={e => updateOption(index, 'label', e.target.value)}
                      placeholder="Label (shown to user)"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => removeOption(index)}
                      disabled={options.length === 1}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* UI Configuration */}
          <div className="space-y-4 border-t border-gray-200 pt-6">
            <h3 className="text-lg font-medium text-gray-900">UI Configuration</h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Placeholder</label>
              <input
                type="text"
                value={uiConfig.placeholder}
                onChange={e => setUiConfig({ ...uiConfig, placeholder: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter a value..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Help Text</label>
              <input
                type="text"
                value={uiConfig.help_text}
                onChange={e => setUiConfig({ ...uiConfig, help_text: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Additional guidance for users"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Field Width</label>
              <select
                value={uiConfig.width}
                onChange={e => setUiConfig({ ...uiConfig, width: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="full">Full Width</option>
                <option value="half">Half Width</option>
                <option value="third">Third Width</option>
              </select>
            </div>
          </div>

          {/* Actions */}
          <div className="border-t border-gray-200 pt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isPending}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isPending && <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />}
              {isEditMode ? 'Update Field' : 'Create Field'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CustomFieldForm;
