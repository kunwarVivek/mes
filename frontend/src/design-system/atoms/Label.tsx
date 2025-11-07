import { LabelHTMLAttributes, forwardRef } from 'react'
import './Label.css'

/**
 * Label Atom
 *
 * A label component for form inputs:
 * - Accessibility: Proper association with inputs
 * - Typography: Clear, readable text
 */

export interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean
}

export const Label = forwardRef<HTMLLabelElement, LabelProps>(
  ({ required = false, className = '', children, ...props }, ref) => {
    return (
      <label ref={ref} className={`label ${className}`} {...props}>
        {children}
        {required && <span className="label__required" aria-label="required">*</span>}
      </label>
    )
  }
)

Label.displayName = 'Label'
