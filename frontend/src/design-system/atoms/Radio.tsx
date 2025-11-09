import { useId, KeyboardEvent } from 'react'
import './Radio.css'

/**
 * Radio Atom
 *
 * A radio button component for mutually exclusive options:
 * - Single Responsibility: Single selection from a group
 * - Accessibility: ARIA radio role, keyboard support
 * - States: checked, unchecked, disabled, focus
 */

export interface RadioProps {
  value: string
  checked: boolean
  onChange: (value: string) => void
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  label?: string
  name: string
  id?: string
}

export const Radio = ({
  value,
  checked,
  onChange,
  disabled = false,
  size = 'md',
  label,
  name,
  id: providedId,
}: RadioProps) => {
  const generatedId = useId()
  const id = providedId || generatedId

  const handleClick = () => {
    if (!disabled) {
      onChange(value)
    }
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (disabled) return

    if (event.key === ' ') {
      event.preventDefault()
      onChange(value)
    }
  }

  const classes = [
    'radio',
    `radio--${size}`,
    checked && 'radio--checked',
    disabled && 'radio--disabled',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="radio-container">
      <div
        className={classes}
        role="radio"
        aria-checked={checked}
        aria-disabled={disabled}
        aria-labelledby={label ? `${id}-label` : undefined}
        tabIndex={disabled ? -1 : 0}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        id={id}
        {...(name && { name })}
      >
        <span className="radio__button">
          {checked && <span className="radio__indicator" />}
        </span>
        <input
          type="radio"
          name={name}
          value={value}
          checked={checked}
          onChange={() => {}}
          tabIndex={-1}
          aria-hidden="true"
          style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
        />
      </div>
      {label && (
        <label htmlFor={id} id={`${id}-label`} className="radio__label">
          {label}
        </label>
      )}
    </div>
  )
}

Radio.displayName = 'Radio'
