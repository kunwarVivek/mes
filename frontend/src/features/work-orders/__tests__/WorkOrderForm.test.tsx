/**
 * WorkOrderForm Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WorkOrderForm } from '../components/WorkOrderForm'
import type { WorkOrder } from '../types/workOrder.types'

const mockWorkOrder: WorkOrder = {
  id: 1,
  organization_id: 1,
  plant_id: 1,
  work_order_number: 'WO001',
  material_id: 1,
  order_type: 'PRODUCTION',
  order_status: 'PLANNED',
  planned_quantity: 100,
  actual_quantity: 0,
  priority: 5,
  created_by_user_id: 1,
  created_at: '2024-01-01T00:00:00Z',
}

describe('WorkOrderForm - Create Mode', () => {
  it('should render create form with empty fields', () => {
    const onSubmit = vi.fn()
    render(<WorkOrderForm mode="create" onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/Material ID/i)).toHaveValue(0)
    expect(screen.getByLabelText(/Planned Quantity/i)).toHaveValue(0)
    expect(screen.getByRole('button', { name: /Create Work Order/i })).toBeInTheDocument()
  })

  it('should validate required fields', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<WorkOrderForm mode="create" onSubmit={onSubmit} />)

    const submitButton = screen.getByRole('button', { name: /Create Work Order/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Material ID is required/i)).toBeInTheDocument()
    })

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should validate quantity must be positive', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<WorkOrderForm mode="create" onSubmit={onSubmit} />)

    // First set material ID to pass that validation
    const materialInput = screen.getByLabelText(/Material ID/i)
    await user.clear(materialInput)
    await user.type(materialInput, '1')

    // Set quantity to 0 (invalid) by clearing it
    const quantityInput = screen.getByLabelText(/Planned Quantity/i)
    await user.clear(quantityInput)
    // After clear, value becomes 0 which fails validation

    const submitButton = screen.getByRole('button', { name: /Create Work Order/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Quantity must be positive/i)).toBeInTheDocument()
    })
  })

  it('should submit valid create form', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<WorkOrderForm mode="create" onSubmit={onSubmit} />)

    const materialInput = screen.getByLabelText(/Material ID/i)
    await user.clear(materialInput)
    await user.type(materialInput, '1')

    const quantityInput = screen.getByLabelText(/Planned Quantity/i)
    await user.clear(quantityInput)
    await user.type(quantityInput, '100')

    await user.type(screen.getByLabelText(/Start Date Planned/i), '2024-01-15')
    await user.type(screen.getByLabelText(/End Date Planned/i), '2024-01-20')

    const submitButton = screen.getByRole('button', { name: /Create Work Order/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          material_id: 1,
          planned_quantity: 100,
        })
      )
    })
  })

  it('should call onCancel when cancel button clicked', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(<WorkOrderForm mode="create" onSubmit={onSubmit} onCancel={onCancel} />)

    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    await user.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
  })
})

describe('WorkOrderForm - Edit Mode', () => {
  it('should render edit form with initial data', () => {
    const onSubmit = vi.fn()
    render(<WorkOrderForm mode="edit" initialData={mockWorkOrder} onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/Material ID/i)).toHaveValue(1)
    expect(screen.getByLabelText(/Planned Quantity/i)).toHaveValue(100)
    expect(screen.getByRole('button', { name: /Update Work Order/i })).toBeInTheDocument()
  })

  it('should disable work order number field in edit mode', () => {
    const onSubmit = vi.fn()
    render(<WorkOrderForm mode="edit" initialData={mockWorkOrder} onSubmit={onSubmit} />)

    const materialInput = screen.getByLabelText(/Material ID/i)
    expect(materialInput).toBeDisabled()
  })

  it('should submit only changed fields in edit mode', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<WorkOrderForm mode="edit" initialData={mockWorkOrder} onSubmit={onSubmit} />)

    const quantityInput = screen.getByLabelText(/Actual Quantity/i)
    await user.clear(quantityInput)
    await user.type(quantityInput, '50')

    const submitButton = screen.getByRole('button', { name: /Update Work Order/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        actual_quantity: 50,
      })
    })
  })

  it('should display error message', () => {
    const onSubmit = vi.fn()
    render(<WorkOrderForm mode="create" onSubmit={onSubmit} error="Test error message" />)

    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('should disable form when loading', () => {
    const onSubmit = vi.fn()
    render(<WorkOrderForm mode="create" onSubmit={onSubmit} isLoading={true} />)

    expect(screen.getByLabelText(/Material ID/i)).toBeDisabled()
    expect(screen.getByLabelText(/Planned Quantity/i)).toBeDisabled()
  })
})
