import { UserCard } from '../molecules'
import type { User } from '@/services/user.service'
import './UserGrid.css'

/**
 * UserGrid Organism
 *
 * Grid layout for displaying multiple user cards:
 * - Gestalt: Similarity creates visual cohesion
 * - Responsive: Adapts to different screen sizes
 * - Grid System: Modern card-based layout
 */

export interface UserGridProps {
  users: User[]
  onDeleteUser?: (id: number) => void
  isDeleting?: boolean
}

export const UserGrid = ({ users, onDeleteUser, isDeleting }: UserGridProps) => {
  return (
    <div className="user-grid">
      {users.map((user) => (
        <UserCard
          key={user.id}
          id={user.id}
          username={user.username}
          email={user.email}
          isActive={user.is_active}
          createdAt={user.created_at}
          onDelete={!isDeleting ? onDeleteUser : undefined}
        />
      ))}
    </div>
  )
}
