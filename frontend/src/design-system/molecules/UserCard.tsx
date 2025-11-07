import { Card, Heading3, Caption } from '../atoms'
import './UserCard.css'

/**
 * UserCard Molecule
 *
 * Displays user information in a card format:
 * - Gestalt: Proximity groups related user data
 * - Visual Hierarchy: Clear information structure
 * - Card-based: Modern, elevated design
 */

export interface UserCardProps {
  id: number
  username: string
  email: string
  isActive: boolean
  createdAt: string
  onDelete?: (id: number) => void
}

export const UserCard = ({
  id,
  username,
  email,
  isActive,
  createdAt,
  onDelete,
}: UserCardProps) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <Card variant="elevated" padding="lg" hoverable>
      <div className="user-card">
        <div className="user-card__header">
          <div className="user-card__avatar">
            {username.charAt(0).toUpperCase()}
          </div>
          <div className="user-card__info">
            <Heading3>{username}</Heading3>
            <Caption>{email}</Caption>
          </div>
        </div>

        <div className="user-card__meta">
          <div className="user-card__status">
            <span
              className={`user-card__status-badge user-card__status-badge--${
                isActive ? 'active' : 'inactive'
              }`}
            >
              {isActive ? 'Active' : 'Inactive'}
            </span>
          </div>
          <Caption>Joined {formatDate(createdAt)}</Caption>
        </div>

        {onDelete && (
          <div className="user-card__actions">
            <button
              onClick={() => onDelete(id)}
              className="user-card__delete-btn"
              aria-label={`Delete ${username}`}
            >
              Delete
            </button>
          </div>
        )}
      </div>
    </Card>
  )
}
