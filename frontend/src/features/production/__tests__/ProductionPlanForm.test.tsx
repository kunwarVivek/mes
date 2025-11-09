/**
 * ProductionPlanForm Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProductionPlanForm } from '../components/ProductionPlanForm'
import type { ProductionPlan } from '../types/production.types'

const mockPlan: ProductionPlan = {
  id: 1,
  organization_id: 1,
  plan_code: 'PLAN001',
  plan_name: 'Q1 Production Plan',
  start_date: '2024-01-01',
  end_date: '2024-03-31',
  status: 'DRAFT',
  created_by_user_id: 1,
  notes: 'Test notes',
  created_at: '2024-01-01T00:00:00Z',
}

describe('ProductionPlanForm - Create Mode', () => {
  it('should render create form with empty fields', () => {
    const onSubmit = vi.fn()
    render(<ProductionPlanForm mode="create" onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/Plan Code/i)).toHaveValue('')
    expect(screen.getByLabelText(/Plan Name/i)).toHaveValue('')
    expect(screen.getByRole('button', { name: /Create Production Plan/i })).toBeInTheDocument()
  })

  it('should validate required fields', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<ProductionPlanForm mode="create" onSubmit={onSubmit} />)

    const submitButton = screen.getByRole('button', { name: /Create Production Plan/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Plan code is required/i)).toBeInTheDocument()
    })

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should validate date range (end date >= start date)', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<ProductionPlanForm mode="create" onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/Plan Code/i), 'PLAN001')
    await user.type(screen.getByLabelText(/Plan Name/i), 'Test Plan')
    await user.type(screen.getByLabelText(/Start Date/i), '2024-06-01')
    await user.type(screen.getByLabelText(/End Date/i), '2024-01-01')

    const submitButton = screen.getByRole('button', { name: /Create Production Plan/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/End date must be after or equal to start date/i)).toBeInTheDocument()
    })

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should submit valid create form', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<ProductionPlanForm mode="create" onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/Plan Code/i), 'PLAN001')
    await user.type(screen.getByLabelText(/Plan Name/i), 'Q1 Production Plan')
    await user.type(screen.getByLabelText(/Start Date/i), '2024-01-01')
    await user.type(screen.getByLabelText(/End Date/i), '2024-03-31')
    await user.selectOptions(screen.getByLabelText(/Status/i), 'DRAFT')

    const submitButton = screen.getByRole('button', { name: /Create Production Plan/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          plan_code: 'PLAN001',
          plan_name: 'Q1 Production Plan',
          start_date: '2024-01-01',
          end_date: '2024-03-31',
          status: 'DRAFT',
        })
      )
    })
  })

  it('should call onCancel when cancel button clicked', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(<ProductionPlanForm mode="create" onSubmit={onSubmit} onCancel={onCancel} />)

    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    await user.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
  })

  it('should render notes field as optional', () => {
    const onSubmit = vi.fn()
    render(<ProductionPlanForm mode="create" onSubmit={onSubmit} />)

    const notesField = screen.getByLabelText(/Notes/i)
    expect(notesField).toBeInTheDocument()
    expect(notesField).not.toBeRequired()
  })
})

describe('ProductionPlanForm - Edit Mode', () => {
  it('should render edit form with initial data', () => {
    const onSubmit = vi.fn()
    render(<ProductionPlanForm mode="edit" initialData={mockPlan} onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/Plan Code/i)).toHaveValue('PLAN001')
    expect(screen.getByLabelText(/Plan Name/i)).toHaveValue('Q1 Production Plan')
    expect(screen.getByRole('button', { name: /Update Production Plan/i })).toBeInTheDocument()
  })

  it('should disable plan code field in edit mode', () => {
    const onSubmit = vi.fn()
    render(<ProductionPlanForm mode="edit" initialData={mockPlan} onSubmit={onSubmit} />)

    const planCodeInput = screen.getByLabelText(/Plan Code/i)
    expect(planCodeInput).toBeDisabled()
  })

  it('should submit only changed fields in edit mode', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<ProductionPlanForm mode="edit" initialData={mockPlan} onSubmit={onSubmit} />)

    const planNameInput = screen.getByLabelText(/Plan Name/i)
    await user.clear(planNameInput)
    await user.type(planNameInput, 'Updated Production Plan')

    const submitButton = screen.getByRole('button', { name: /Update Production Plan/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        plan_name: 'Updated Production Plan',
      })
    })
  })

  it('should display error message', () => {
    const onSubmit = vi.fn()
    render(<ProductionPlanForm mode="create" onSubmit={onSubmit} error="Test error message" />)

    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('should disable form when loading', () => {
    const onSubmit = vi.fn()
    render(<ProductionPlanForm mode="create" onSubmit={onSubmit} isLoading={true} />)

    expect(screen.getByLabelText(/Plan Code/i)).toBeDisabled()
    expect(screen.getByLabelText(/Plan Name/i)).toBeDisabled()
  })

  it('should render all status options', () => {
    const onSubmit = vi.fn()
    render(<ProductionPlanForm mode="create" onSubmit={onSubmit} />)

    const statusSelect = screen.getByLabelText(/Status/i)
    expect(statusSelect).toBeInTheDocument()

    const options = Array.from(statusSelect.querySelectorAll('option')).map(opt => opt.value)
    expect(options).toEqual(['DRAFT', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'])
  })
})
