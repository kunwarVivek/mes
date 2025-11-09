import { ChangeEvent } from 'react'
import './Textarea.css'

/**
 * Textarea Atom
 *
 * A multi-line text input component:
 * - Single Responsibility: Multi-line text entry
 * - Accessibility: ARIA attributes for errors and descriptions
 * - Features: Character counter, resize options, error states
 */

export interface TextareaProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  rows?: number
  maxLength?: number
  resize?: 'none' | 'vertical' | 'horizontal' | 'both'
  error?: boolean
  id?: string
  name?: string
  className?: string
}

export const Textarea = ({
  value,
  onChange,
  placeholder,
  disabled = false,
  rows = 3,
  maxLength,
  resize = 'vertical',
  error = false,
  id,
  name,
  className = '',
}: TextareaProps) => {
  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = event.target.value
    if (maxLength && newValue.length > maxLength) {
      return
    }
    onChange(newValue)
  }

  const classes = [
    'textarea',
    `textarea--resize-${resize}`,
    error && 'textarea--error',
    disabled && 'textarea--disabled',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="textarea-container">
      <textarea
        id={id}
        name={name}
        className={classes}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        rows={rows}
        maxLength={maxLength}
        aria-invalid={error}
      />
      {maxLength && (
        <div className="textarea__counter">
          {value.length} / {maxLength}
        </div>
      )}
    </div>
  )
}

Textarea.displayName = 'Textarea'
