/**
 * ProjectsPage Component
 *
 * Main page for managing projects with CRUD operations
 */
import { useState, useEffect, useRef } from 'react'
import { Button, Heading1 } from '../../../design-system/atoms'
import { ProjectsTable } from '../components/ProjectsTable'
import { ProjectForm } from '../components/ProjectForm'
import {
  useProjects,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
} from '../hooks/useProjects'
import { ProjectStatus } from '../types/project.types'
import type { Project, ProjectCreateRequest, ProjectUpdateRequest } from '../types/project.types'
import { useAuthStore } from '../../../stores/auth.store'

export function ProjectsPage() {
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | 'ALL'>('ALL')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null)
  const formModalRef = useRef<HTMLDivElement>(null)
  const deleteModalRef = useRef<HTMLDivElement>(null)

  const currentPlant = useAuthStore((state) => state.currentPlant)
  const queryFilters = statusFilter === 'ALL' ? {} : { status: statusFilter }
  const { data, isLoading } = useProjects(queryFilters)
  const createMutation = useCreateProject()
  const updateMutation = useUpdateProject()
  const deleteMutation = useDeleteProject()

  const handleCreate = () => {
    setEditingProject(null)
    setIsFormOpen(true)
  }

  const handleEdit = (project: Project) => {
    setEditingProject(project)
    setIsFormOpen(true)
  }

  const handleDelete = (id: number) => {
    setShowDeleteConfirm(id)
  }

  const confirmDelete = async () => {
    if (showDeleteConfirm) {
      try {
        await deleteMutation.mutateAsync(showDeleteConfirm)
        setShowDeleteConfirm(null)
      } catch (error) {
        console.error('Failed to delete project:', error)
        alert('Failed to delete project. Please try again.')
      }
    }
  }

  const handleSubmit = async (formData: ProjectCreateRequest | ProjectUpdateRequest) => {
    if (editingProject) {
      await updateMutation.mutateAsync({
        id: editingProject.id,
        data: formData,
      })
    } else {
      await createMutation.mutateAsync(formData)
    }
    setIsFormOpen(false)
    setEditingProject(null)
  }

  const handleCancel = () => {
    setIsFormOpen(false)
    setEditingProject(null)
  }

  const isSubmitting = createMutation.isPending || updateMutation.isPending

  // Focus trap for modals
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (isFormOpen) {
          handleCancel()
        } else if (showDeleteConfirm) {
          setShowDeleteConfirm(null)
        }
      }
    }

    if (isFormOpen || showDeleteConfirm) {
      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isFormOpen, showDeleteConfirm])

  // Focus management for modals
  useEffect(() => {
    if (isFormOpen && formModalRef.current) {
      const focusableElements = formModalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      const firstElement = focusableElements[0] as HTMLElement
      firstElement?.focus()
    }
  }, [isFormOpen])

  useEffect(() => {
    if (showDeleteConfirm && deleteModalRef.current) {
      const focusableElements = deleteModalRef.current.querySelectorAll('button')
      const firstElement = focusableElements[0] as HTMLElement
      firstElement?.focus()
    }
  }, [showDeleteConfirm])

  if (!currentPlant) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-gray-600">Please select a plant to view projects</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <Heading1>Projects</Heading1>
        <Button onClick={handleCreate}>New Project</Button>
      </div>

      <div className="mb-4">
        <label htmlFor="status-filter" className="mr-2 text-sm font-medium text-gray-700">
          Filter by Status:
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as ProjectStatus | 'ALL')}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="ALL">All</option>
          {Object.values(ProjectStatus).map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>

      {isFormOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="form-modal-title"
        >
          <div
            ref={formModalRef}
            className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
            <h2 id="form-modal-title" className="text-2xl font-bold mb-4">
              {editingProject ? 'Edit Project' : 'New Project'}
            </h2>
            <ProjectForm
              project={editingProject}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              isLoading={isSubmitting}
            />
          </div>
        </div>
      )}

      {showDeleteConfirm && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-modal-title"
        >
          <div
            ref={deleteModalRef}
            className="bg-white rounded-lg p-6 max-w-md w-full"
          >
            <h2 id="delete-modal-title" className="text-xl font-bold mb-4">Confirm Delete</h2>
            <p className="mb-6">Are you sure you want to delete this project? This action cannot be undone.</p>
            <div className="flex justify-end space-x-3">
              <Button variant="outline" onClick={() => setShowDeleteConfirm(null)}>
                Cancel
              </Button>
              <Button onClick={confirmDelete} disabled={deleteMutation.isPending}>
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}

      <ProjectsTable
        projects={data?.items || []}
        isLoading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
    </div>
  )
}
