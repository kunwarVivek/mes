import { Body, Heading2 } from '../atoms'
import './EmptyState.css'

/**
 * EmptyState Molecule
 *
 * Displays empty state with message and optional action:
 * - Visual Feedback: Clear communication of empty state
 * - Gestalt: Centered, balanced composition
 */

export interface EmptyStateProps {
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export const EmptyState = ({ title, description, action }: EmptyStateProps) => {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">
        <svg
          width="64"
          height="64"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <Heading2>{title}</Heading2>
      {description && <Body>{description}</Body>}
      {action && (
        <button onClick={action.onClick} className="empty-state__action">
          {action.label}
        </button>
      )}
    </div>
  )
}
