import { useId, KeyboardEvent } from 'react'
import './Switch.css'

/**
 * Switch Atom
 *
 * A toggle switch component for binary on/off states:
 * - Single Responsibility: Toggle state management
 * - Accessibility: ARIA switch role, keyboard support
 * - States: checked, unchecked, disabled, focus
 */

export interface SwitchProps {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  label?: string
  id?: string
  name?: string
}

export const Switch = ({
  checked,
  onChange,
  disabled = false,
  size = 'md',
  label,
  id: providedId,
  name,
}: SwitchProps) => {
  const generatedId = useId()
  const id = providedId || generatedId

  const handleClick = () => {
    if (!disabled) {
      onChange(!checked)
    }
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (disabled) return

    if (event.key === ' ' || event.key === 'Enter') {
      event.preventDefault()
      onChange(!checked)
    }
  }

  const classes = [
    'switch',
    `switch--${size}`,
    checked && 'switch--checked',
    disabled && 'switch--disabled',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="switch-container">
      <div
        className={classes}
        role="switch"
        aria-checked={checked}
        aria-disabled={disabled}
        aria-labelledby={label ? `${id}-label` : undefined}
        tabIndex={disabled ? -1 : 0}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        id={id}
        {...(name && { name })}
      >
        <span className="switch__track">
          <span className="switch__thumb" />
        </span>
        {name && (
          <input
            type="checkbox"
            name={name}
            checked={checked}
            onChange={() => {}}
            tabIndex={-1}
            style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
          />
        )}
      </div>
      {label && (
        <label htmlFor={id} id={`${id}-label`} className="switch__label">
          {label}
        </label>
      )}
    </div>
  )
}

Switch.displayName = 'Switch'
