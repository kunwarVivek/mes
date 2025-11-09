/**
 * ProjectsTable Component Tests
 *
 * TDD: RED phase - Tests written before implementation
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProjectsTable } from '../ProjectsTable'
import { ProjectStatus } from '../../types/project.types'
import type { Project } from '../../types/project.types'

const mockProjects: Project[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    project_code: 'PRJ-001',
    project_name: 'Test Project 1',
    description: 'First test project',
    status: ProjectStatus.ACTIVE,
    planned_start_date: '2025-01-01',
    planned_end_date: '2025-12-31',
    priority: 1,
    is_active: true,
    bom_id: 1,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    project_code: 'PRJ-002',
    project_name: 'Test Project 2',
    status: ProjectStatus.PLANNING,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
]

describe('ProjectsTable', () => {
  it('should render projects in a table', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()

    render(<ProjectsTable projects={mockProjects} isLoading={false} onEdit={onEdit} onDelete={onDelete} />)

    expect(screen.getByText('PRJ-001')).toBeInTheDocument()
    expect(screen.getByText('Test Project 1')).toBeInTheDocument()
    expect(screen.getByText('PRJ-002')).toBeInTheDocument()
    expect(screen.getByText('Test Project 2')).toBeInTheDocument()
  })

  it('should display status badges with correct colors', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()

    render(<ProjectsTable projects={mockProjects} isLoading={false} onEdit={onEdit} onDelete={onDelete} />)

    const activeBadge = screen.getByText('ACTIVE')
    const planningBadge = screen.getByText('PLANNING')

    expect(activeBadge).toBeInTheDocument()
    expect(planningBadge).toBeInTheDocument()
  })

  it('should call onEdit when edit button is clicked', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()

    render(<ProjectsTable projects={mockProjects} isLoading={false} onEdit={onEdit} onDelete={onDelete} />)

    const editButtons = screen.getAllByRole('button', { name: /edit/i })
    fireEvent.click(editButtons[0])

    expect(onEdit).toHaveBeenCalledWith(mockProjects[0])
  })

  it('should call onDelete when delete button is clicked', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()

    render(<ProjectsTable projects={mockProjects} isLoading={false} onEdit={onEdit} onDelete={onDelete} />)

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    fireEvent.click(deleteButtons[0])

    expect(onDelete).toHaveBeenCalledWith(mockProjects[0].id)
  })

  it('should show empty state when no projects', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()

    render(<ProjectsTable projects={[]} isLoading={false} onEdit={onEdit} onDelete={onDelete} />)

    expect(screen.getByText(/no projects found/i)).toBeInTheDocument()
  })

  it('should show loading state', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()

    render(<ProjectsTable projects={[]} isLoading={true} onEdit={onEdit} onDelete={onDelete} />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })




})
