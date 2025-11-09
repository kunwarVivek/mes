import { useId, KeyboardEvent } from 'react'
import './Checkbox.css'

/**
 * Checkbox Atom
 *
 * A checkbox component with support for indeterminate state:
 * - Single Responsibility: Boolean selection with partial state
 * - Accessibility: ARIA checkbox role, keyboard support
 * - States: checked, unchecked, indeterminate, disabled, focus
 */

export interface CheckboxProps {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  indeterminate?: boolean
  size?: 'sm' | 'md' | 'lg'
  label?: string
  name?: string
  id?: string
}

export const Checkbox = ({
  checked,
  onChange,
  disabled = false,
  indeterminate = false,
  size = 'md',
  label,
  name,
  id: providedId,
}: CheckboxProps) => {
  const generatedId = useId()
  const id = providedId || generatedId

  const handleClick = () => {
    if (!disabled) {
      onChange(!checked)
    }
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (disabled) return

    if (event.key === ' ') {
      event.preventDefault()
      onChange(!checked)
    }
  }

  const classes = [
    'checkbox',
    `checkbox--${size}`,
    checked && 'checkbox--checked',
    indeterminate && 'checkbox--indeterminate',
    disabled && 'checkbox--disabled',
  ]
    .filter(Boolean)
    .join(' ')

  const ariaChecked = indeterminate ? 'mixed' : checked

  return (
    <div className="checkbox-container">
      <div
        className={classes}
        role="checkbox"
        aria-checked={ariaChecked}
        aria-disabled={disabled}
        aria-labelledby={label ? `${id}-label` : undefined}
        tabIndex={disabled ? -1 : 0}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        id={id}
        {...(name && { name })}
      >
        <span className="checkbox__box">
          {checked && !indeterminate && (
            <svg
              className="checkbox__icon checkbox__icon--check"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M13 4L6 11L3 8"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
          {indeterminate && (
            <svg
              className="checkbox__icon checkbox__icon--indeterminate"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M4 8H12"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          )}
        </span>
        {name && (
          <input
            type="checkbox"
            name={name}
            checked={checked}
            onChange={() => {}}
            tabIndex={-1}
            aria-hidden="true"
            style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
          />
        )}
      </div>
      {label && (
        <label htmlFor={id} id={`${id}-label`} className="checkbox__label">
          {label}
        </label>
      )}
    </div>
  )
}

Checkbox.displayName = 'Checkbox'
