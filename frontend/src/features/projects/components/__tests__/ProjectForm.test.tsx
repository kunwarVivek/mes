/**
 * ProjectForm Component Tests
 *
 * TDD: Testing form validation and submission
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ProjectForm } from '../ProjectForm'
import { ProjectStatus } from '../../types/project.types'
import type { Project } from '../../types/project.types'

const mockProject: Project = {
  id: 1,
  organization_id: 1,
  plant_id: 1,
  project_code: 'PRJ-001',
  project_name: 'Test Project',
  description: 'Test description',
  status: ProjectStatus.ACTIVE,
  planned_planned_start_date: '2025-01-01',
    planned_planned_end_date: '2025-12-31',
    priority: 1,
    is_active: true,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
}

describe('ProjectForm', () => {
  it('should render form fields for new project', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ProjectForm onSubmit={onSubmit} onCancel={onCancel} isLoading={false} />)

    expect(screen.getByLabelText(/project code/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/project name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/status/i)).toBeInTheDocument()
    expect(screen.getByText(/create project/i)).toBeInTheDocument()
  })

  it('should populate form with project data when editing', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ProjectForm project={mockProject} onSubmit={onSubmit} onCancel={onCancel} isLoading={false} />)

    expect(screen.getByDisplayValue('PRJ-001')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Test Project')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Test description')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Test Project')).toBeInTheDocument()
    expect(screen.getByText(/update project/i)).toBeInTheDocument()
  })

  it('should disable project code field when editing', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ProjectForm project={mockProject} onSubmit={onSubmit} onCancel={onCancel} isLoading={false} />)

    const projectCodeInput = screen.getByDisplayValue('PRJ-001')
    expect(projectCodeInput).toBeDisabled()
  })

  it('should validate required fields', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ProjectForm onSubmit={onSubmit} onCancel={onCancel} isLoading={false} />)

    const submitButton = screen.getByText(/create project/i)
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/project code is required/i)).toBeInTheDocument()
      expect(screen.getByText(/project name is required/i)).toBeInTheDocument()
    })

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should validate end date is after start date', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ProjectForm onSubmit={onSubmit} onCancel={onCancel} isLoading={false} />)

    const projectCodeInput = screen.getByLabelText(/project code/i)
    const projectNameInput = screen.getByLabelText(/project name/i)
    const startDateInput = screen.getByLabelText(/start date/i)
    const endDateInput = screen.getByLabelText(/end date/i)

    fireEvent.change(projectCodeInput, { target: { value: 'PRJ-001' } })
    fireEvent.change(projectNameInput, { target: { value: 'Test Project' } })
    fireEvent.change(startDateInput, { target: { value: '2025-12-31' } })
    fireEvent.change(endDateInput, { target: { value: '2025-01-01' } })

    const submitButton = screen.getByText(/create project/i)
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/planned end date must be on or after planned start date/i)).toBeInTheDocument()
    })

    expect(onSubmit).not.toHaveBeenCalled()
  })



  it('should submit valid form data', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const onCancel = vi.fn()

    render(<ProjectForm onSubmit={onSubmit} onCancel={onCancel} isLoading={false} />)

    const projectCodeInput = screen.getByLabelText(/project code/i)
    const projectNameInput = screen.getByLabelText(/project name/i)

    fireEvent.change(projectCodeInput, { target: { value: 'PRJ-001' } })
    fireEvent.change(projectNameInput, { target: { value: 'Test Project' } })

    const submitButton = screen.getByText(/create project/i)
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          project_code: 'PRJ-001',
          project_name: 'Test Project',
        })
      )
    })
  })

  it('should call onCancel when cancel button is clicked', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ProjectForm onSubmit={onSubmit} onCancel={onCancel} isLoading={false} />)

    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    fireEvent.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should disable form when loading', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ProjectForm onSubmit={onSubmit} onCancel={onCancel} isLoading={true} />)

    expect(screen.getByLabelText(/project code/i)).toBeDisabled()
    expect(screen.getByLabelText(/project name/i)).toBeDisabled()
    expect(screen.getByText(/saving/i)).toBeInTheDocument()
  })
})
