import React from 'react';
import type { CustomField } from '@/types/customFields';

interface DynamicFieldInputProps {
  field: CustomField;
  value: any;
  onChange: (value: any) => void;
  error?: string;
  disabled?: boolean;
}

/**
 * Dynamic Field Input Component
 *
 * Renders the appropriate input component based on field type.
 * Supports all custom field types with validation.
 */
export const DynamicFieldInput: React.FC<DynamicFieldInputProps> = ({
  field,
  value,
  onChange,
  error,
  disabled = false,
}) => {
  const inputClasses = `w-full px-3 py-2 border ${
    error ? 'border-red-500' : 'border-gray-300'
  } rounded-md focus:outline-none focus:ring-2 ${
    error ? 'focus:ring-red-500' : 'focus:ring-blue-500'
  } disabled:bg-gray-100 disabled:cursor-not-allowed`;

  const placeholder = field.ui_config?.placeholder || '';
  const helpText = field.ui_config?.help_text || '';

  const renderInput = () => {
    switch (field.field_type) {
      case 'text':
      case 'email':
      case 'url':
      case 'phone':
        return (
          <input
            type={field.field_type}
            value={value || ''}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
            required={field.is_required}
            disabled={disabled}
            className={inputClasses}
            minLength={field.validation_rules?.min_length}
            maxLength={field.validation_rules?.max_length}
            pattern={field.validation_rules?.pattern}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={value || ''}
            onChange={e => onChange(e.target.value ? Number(e.target.value) : null)}
            placeholder={placeholder}
            required={field.is_required}
            disabled={disabled}
            className={inputClasses}
            min={field.validation_rules?.min_value}
            max={field.validation_rules?.max_value}
            step="any"
          />
        );

      case 'textarea':
        return (
          <textarea
            value={value || ''}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
            required={field.is_required}
            disabled={disabled}
            className={inputClasses}
            rows={4}
            minLength={field.validation_rules?.min_length}
            maxLength={field.validation_rules?.max_length}
          />
        );

      case 'date':
        return (
          <input
            type="date"
            value={value || ''}
            onChange={e => onChange(e.target.value)}
            required={field.is_required}
            disabled={disabled}
            className={inputClasses}
            min={field.validation_rules?.date_range?.min}
            max={field.validation_rules?.date_range?.max}
          />
        );

      case 'datetime':
        return (
          <input
            type="datetime-local"
            value={value || ''}
            onChange={e => onChange(e.target.value)}
            required={field.is_required}
            disabled={disabled}
            className={inputClasses}
          />
        );

      case 'select':
        return (
          <select
            value={value || ''}
            onChange={e => onChange(e.target.value)}
            required={field.is_required}
            disabled={disabled}
            className={inputClasses}
          >
            <option value="">-- Select --</option>
            {field.options?.map(option => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'multiselect':
        return (
          <select
            multiple
            value={value || []}
            onChange={e => {
              const selected = Array.from(e.target.selectedOptions, option => option.value);
              onChange(selected);
            }}
            required={field.is_required}
            disabled={disabled}
            className={`${inputClasses} min-h-[120px]`}
          >
            {field.options?.map(option => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'boolean':
        return (
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value || false}
              onChange={e => onChange(e.target.checked)}
              disabled={disabled}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:cursor-not-allowed"
            />
            <span className="text-sm text-gray-700">
              {field.ui_config?.placeholder || 'Yes'}
            </span>
          </label>
        );

      case 'file':
        return (
          <input
            type="file"
            onChange={e => onChange(e.target.files?.[0] || null)}
            required={field.is_required}
            disabled={disabled}
            className={inputClasses}
            accept={field.validation_rules?.allowed_file_types?.map(t => `.${t}`).join(',')}
          />
        );

      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
            required={field.is_required}
            disabled={disabled}
            className={inputClasses}
          />
        );
    }
  };

  // Determine field width
  const widthClasses = {
    full: 'col-span-full',
    half: 'col-span-full md:col-span-1',
    third: 'col-span-full md:col-span-1 lg:col-span-1',
  };
  const widthClass = widthClasses[field.ui_config?.width || 'full'];

  return (
    <div className={widthClass}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {field.field_label}
        {field.is_required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {renderInput()}
      {helpText && !error && (
        <p className="text-xs text-gray-500 mt-1">{helpText}</p>
      )}
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
};

export default DynamicFieldInput;
