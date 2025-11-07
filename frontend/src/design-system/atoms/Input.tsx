import { InputHTMLAttributes, forwardRef } from 'react'
import './Input.css'

/**
 * Input Atom
 *
 * A reusable input component following design principles:
 * - Single Responsibility: Text input
 * - Accessibility: Proper labeling and error states
 * - Validation: Visual feedback for errors
 */

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
  fullWidth?: boolean
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ error = false, fullWidth = false, className = '', ...props }, ref) => {
    const classes = [
      'input',
      error && 'input--error',
      fullWidth && 'input--full-width',
      className,
    ]
      .filter(Boolean)
      .join(' ')

    return (
      <input
        ref={ref}
        className={classes}
        aria-invalid={error}
        {...props}
      />
    )
  }
)

Input.displayName = 'Input'
