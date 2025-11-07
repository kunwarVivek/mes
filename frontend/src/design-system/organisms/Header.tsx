import { Button, Heading1 } from '../atoms'
import './Header.css'

/**
 * Header Organism
 *
 * Application header with navigation:
 * - Visual Hierarchy: Clear page title and actions
 * - Gestalt: Continuity across top of page
 */

export interface HeaderProps {
  title: string
  action?: {
    label: string
    onClick: () => void
  }
}

export const Header = ({ title, action }: HeaderProps) => {
  return (
    <header className="header">
      <div className="header__content">
        <Heading1>{title}</Heading1>
        {action && (
          <Button onClick={action.onClick} variant="primary">
            {action.label}
          </Button>
        )}
      </div>
    </header>
  )
}
