/**
 * ProjectForm Component
 *
 * Form for creating/editing projects with validation
 * Aligned with backend DTOs
 */
import { useState, useEffect } from 'react'
import { Button, Input, Textarea, Label } from '../../../design-system/atoms'
import { ProjectStatus } from '../types/project.types'
import type { Project, ProjectCreateRequest, ProjectUpdateRequest } from '../types/project.types'
import { useAuthStore } from '../../../stores/auth.store'

interface ProjectFormProps {
  project?: Project | null
  onSubmit: (data: ProjectCreateRequest | ProjectUpdateRequest) => Promise<void>
  onCancel: () => void
  isLoading: boolean
}

interface FormData {
  organization_id: number
  plant_id: number
  project_code: string
  project_name: string
  description: string
  status: ProjectStatus
  planned_start_date: string
  planned_end_date: string
  actual_start_date: string
  actual_end_date: string
  priority: string
  is_active: boolean
  bom_id: string
}

interface FormErrors {
  project_code?: string
  project_name?: string
  planned_end_date?: string
  priority?: string
}

function validateForm(data: FormData, isEdit: boolean): FormErrors {
  const errors: FormErrors = {}

  if (!isEdit && !data.project_code) {
    errors.project_code = 'Project code is required'
  }
  if (!isEdit && data.project_code.length > 50) {
    errors.project_code = 'Project code must be 50 characters or less'
  }

  if (!data.project_name) {
    errors.project_name = 'Project name is required'
  }
  if (data.project_name.length > 200) {
    errors.project_name = 'Project name must be 200 characters or less'
  }

  if (data.planned_start_date && data.planned_end_date && data.planned_end_date < data.planned_start_date) {
    errors.planned_end_date = 'Planned end date must be on or after planned start date'
  }

  if (data.priority && parseInt(data.priority) < 0) {
    errors.priority = 'Priority must be 0 or greater'
  }

  return errors
}

export function ProjectForm({ project, onSubmit, onCancel, isLoading }: ProjectFormProps) {
  const isEdit = !!project
  const currentPlant = useAuthStore((state) => state.currentPlant)
  const currentOrg = useAuthStore((state) => state.currentOrg)

  const [formData, setFormData] = useState<FormData>({
    organization_id: project?.organization_id || currentOrg?.id || 0,
    plant_id: project?.plant_id || currentPlant?.id || 0,
    project_code: project?.project_code || '',
    project_name: project?.project_name || '',
    description: project?.description || '',
    status: project?.status || ProjectStatus.PLANNING,
    planned_start_date: project?.planned_start_date || '',
    planned_end_date: project?.planned_end_date || '',
    actual_start_date: project?.actual_start_date || '',
    actual_end_date: project?.actual_end_date || '',
    priority: project?.priority?.toString() || '0',
    is_active: project?.is_active ?? true,
    bom_id: project?.bom_id?.toString() || '',
  })

  const [errors, setErrors] = useState<FormErrors>({})

  useEffect(() => {
    if (project) {
      setFormData({
        organization_id: project.organization_id,
        plant_id: project.plant_id,
        project_code: project.project_code,
        project_name: project.project_name,
        description: project.description || '',
        status: project.status,
        planned_start_date: project.planned_start_date || '',
        planned_end_date: project.planned_end_date || '',
        actual_start_date: project.actual_start_date || '',
        actual_end_date: project.actual_end_date || '',
        priority: project.priority?.toString() || '0',
        is_active: project.is_active ?? true,
        bom_id: project.bom_id?.toString() || '',
      })
    }
  }, [project])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const validationErrors = validateForm(formData, isEdit)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const submitData: ProjectCreateRequest | ProjectUpdateRequest = isEdit
      ? {
          project_name: formData.project_name,
          description: formData.description || undefined,
          status: formData.status,
          planned_start_date: formData.planned_start_date || undefined,
          planned_end_date: formData.planned_end_date || undefined,
          actual_start_date: formData.actual_start_date || undefined,
          actual_end_date: formData.actual_end_date || undefined,
          priority: formData.priority ? parseInt(formData.priority) : undefined,
          is_active: formData.is_active,
          bom_id: formData.bom_id ? parseInt(formData.bom_id) : undefined,
        }
      : {
          organization_id: formData.organization_id,
          plant_id: formData.plant_id,
          project_code: formData.project_code,
          project_name: formData.project_name,
          description: formData.description || undefined,
          status: formData.status,
          planned_start_date: formData.planned_start_date || undefined,
          planned_end_date: formData.planned_end_date || undefined,
          priority: formData.priority ? parseInt(formData.priority) : undefined,
          bom_id: formData.bom_id ? parseInt(formData.bom_id) : undefined,
        }

    await onSubmit(submitData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="project_code">Project Code *</Label>
        <Input
          id="project_code"
          value={formData.project_code}
          onChange={(e) => setFormData({ ...formData, project_code: e.target.value })}
          disabled={isEdit || isLoading}
          aria-invalid={!!errors.project_code}
        />
        {errors.project_code && <p className="text-red-500 text-sm mt-1">{errors.project_code}</p>}
      </div>

      <div>
        <Label htmlFor="project_name">Project Name *</Label>
        <Input
          id="project_name"
          value={formData.project_name}
          onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
          disabled={isLoading}
          aria-invalid={!!errors.project_name}
        />
        {errors.project_name && <p className="text-red-500 text-sm mt-1">{errors.project_name}</p>}
      </div>

      <div>
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          disabled={isLoading}
          rows={3}
        />
      </div>

      <div>
        <Label htmlFor="status">Status</Label>
        <select
          id="status"
          value={formData.status}
          onChange={(e) => setFormData({ ...formData, status: e.target.value as ProjectStatus })}
          disabled={isLoading}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {Object.values(ProjectStatus).map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="planned_start_date">Planned Start Date</Label>
          <Input
            id="planned_start_date"
            type="date"
            value={formData.planned_start_date}
            onChange={(e) => setFormData({ ...formData, planned_start_date: e.target.value })}
            disabled={isLoading}
          />
        </div>

        <div>
          <Label htmlFor="planned_end_date">Planned End Date</Label>
          <Input
            id="planned_end_date"
            type="date"
            value={formData.planned_end_date}
            onChange={(e) => setFormData({ ...formData, planned_end_date: e.target.value })}
            disabled={isLoading}
            aria-invalid={!!errors.planned_end_date}
          />
          {errors.planned_end_date && <p className="text-red-500 text-sm mt-1">{errors.planned_end_date}</p>}
        </div>
      </div>

      {isEdit && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="actual_start_date">Actual Start Date</Label>
            <Input
              id="actual_start_date"
              type="date"
              value={formData.actual_start_date}
              onChange={(e) => setFormData({ ...formData, actual_start_date: e.target.value })}
              disabled={isLoading}
            />
          </div>

          <div>
            <Label htmlFor="actual_end_date">Actual End Date</Label>
            <Input
              id="actual_end_date"
              type="date"
              value={formData.actual_end_date}
              onChange={(e) => setFormData({ ...formData, actual_end_date: e.target.value })}
              disabled={isLoading}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="priority">Priority</Label>
          <Input
            id="priority"
            type="number"
            min="0"
            step="1"
            value={formData.priority}
            onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
            disabled={isLoading}
            aria-invalid={!!errors.priority}
          />
          {errors.priority && <p className="text-red-500 text-sm mt-1">{errors.priority}</p>}
        </div>

        <div>
          <Label htmlFor="bom_id">BOM ID (Optional)</Label>
          <Input
            id="bom_id"
            type="number"
            value={formData.bom_id}
            onChange={(e) => setFormData({ ...formData, bom_id: e.target.value })}
            disabled={isLoading}
          />
        </div>
      </div>

      {isEdit && (
        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_active"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
            disabled={isLoading}
            className="mr-2"
          />
          <Label htmlFor="is_active">Active</Label>
        </div>
      )}

      <div className="flex justify-end space-x-3 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Saving...' : isEdit ? 'Update Project' : 'Create Project'}
        </Button>
      </div>
    </form>
  )
}
