import { InputHTMLAttributes } from 'react'
import { Input, Label } from '../atoms'
import './FormField.css'

/**
 * FormField Molecule
 *
 * Combines Label + Input + Error Message:
 * - Proximity: Groups related form elements
 * - Single Responsibility: Complete form field unit
 * - Accessibility: Proper label-input association
 */

export interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  helperText?: string
}

export const FormField = ({
  label,
  error,
  helperText,
  required,
  id,
  ...inputProps
}: FormFieldProps) => {
  const fieldId = id || `field-${label.toLowerCase().replace(/\s+/g, '-')}`

  return (
    <div className="form-field">
      <Label htmlFor={fieldId} required={required}>
        {label}
      </Label>
      <Input
        id={fieldId}
        error={!!error}
        aria-describedby={error ? `${fieldId}-error` : helperText ? `${fieldId}-helper` : undefined}
        {...inputProps}
      />
      {error && (
        <span id={`${fieldId}-error`} className="form-field__error" role="alert">
          {error}
        </span>
      )}
      {helperText && !error && (
        <span id={`${fieldId}-helper`} className="form-field__helper">
          {helperText}
        </span>
      )}
    </div>
  )
}
