import { useState } from 'react'
import { useUsers, useCreateUser, useDeleteUser } from '@/hooks/useUsers'
import { Header, UserForm, UserGrid } from '@/design-system/organisms'
import { EmptyState } from '@/design-system/molecules'
import { Body } from '@/design-system/atoms'
import type { CreateUserDto } from '@/services/user.service'
import './UsersPage.css'

/**
 * UsersPage
 *
 * Main page for user management:
 * - Composed of organisms and molecules
 * - Single Responsibility: User CRUD operations
 * - State Management: TanStack Query for server state
 */

export const UsersPage = () => {
  const [showForm, setShowForm] = useState(false)
  const { data: users, isLoading, error } = useUsers()
  const createUser = useCreateUser()
  const deleteUser = useDeleteUser()

  const handleCreateUser = async (data: CreateUserDto) => {
    await createUser.mutateAsync(data)
    setShowForm(false)
  }

  const handleDeleteUser = (id: number) => {
    if (confirm('Are you sure you want to delete this user?')) {
      deleteUser.mutate(id)
    }
  }

  if (isLoading) {
    return (
      <div className="users-page">
        <Header title="Users" />
        <main className="users-page__content">
          <div className="users-page__loading">
            <Body>Loading users...</Body>
          </div>
        </main>
      </div>
    )
  }

  if (error) {
    return (
      <div className="users-page">
        <Header title="Users" />
        <main className="users-page__content">
          <EmptyState
            title="Error Loading Users"
            description={(error as Error).message}
            action={{ label: 'Retry', onClick: () => window.location.reload() }}
          />
        </main>
      </div>
    )
  }

  return (
    <div className="users-page">
      <Header
        title="Users"
        action={{
          label: showForm ? 'View Users' : 'Create User',
          onClick: () => setShowForm(!showForm),
        }}
      />

      <main className="users-page__content">
        {showForm ? (
          <UserForm
            onSubmit={handleCreateUser}
            onCancel={() => setShowForm(false)}
            isLoading={createUser.isPending}
            error={createUser.error ? (createUser.error as any)?.response?.data?.detail : undefined}
          />
        ) : users && users.length > 0 ? (
          <UserGrid
            users={users}
            onDeleteUser={handleDeleteUser}
            isDeleting={deleteUser.isPending}
          />
        ) : (
          <EmptyState
            title="No Users Found"
            description="Get started by creating your first user"
            action={{ label: 'Create User', onClick: () => setShowForm(true) }}
          />
        )}
      </main>
    </div>
  )
}
