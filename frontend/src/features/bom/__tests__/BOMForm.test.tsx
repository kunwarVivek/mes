/**
 * BOMForm Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BOMForm } from '../components/BOMForm'
import type { BOM } from '../types/bom.types'

const mockBOM: BOM = {
  id: 1,
  organization_id: 1,
  plant_id: 1,
  bom_number: 'BOM001',
  material_id: 1,
  bom_version: 1,
  bom_name: 'Test BOM',
  bom_type: 'PRODUCTION',
  base_quantity: 1,
  unit_of_measure_id: 1,
  is_active: true,
  created_by_user_id: 1,
  created_at: '2024-01-01T00:00:00Z',
}

describe('BOMForm - Create Mode', () => {
  it('should render create form with empty fields', () => {
    const onSubmit = vi.fn()
    render(<BOMForm mode="create" onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/BOM Number/i)).toHaveValue('')
    expect(screen.getByLabelText(/BOM Name/i)).toHaveValue('')
    expect(screen.getByRole('button', { name: /Create BOM/i })).toBeInTheDocument()
  })

  it('should validate required fields', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<BOMForm mode="create" onSubmit={onSubmit} />)

    const submitButton = screen.getByRole('button', { name: /Create BOM/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/BOM number is required/i)).toBeInTheDocument()
    })

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should validate BOM number format', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<BOMForm mode="create" onSubmit={onSubmit} />)

    const bomNumberInput = screen.getByLabelText(/BOM Number/i)
    await user.type(bomNumberInput, 'a'.repeat(51))

    const submitButton = screen.getByRole('button', { name: /Create BOM/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(
        screen.getByText(/BOM number must be at most 50 characters/i)
      ).toBeInTheDocument()
    })
  })

  it('should submit valid create form', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<BOMForm mode="create" onSubmit={onSubmit} defaultOrgId={1} defaultPlantId={1} />)

    // Clear and fill required fields
    const bomNumberInput = screen.getByLabelText(/BOM Number/i)
    const bomNameInput = screen.getByLabelText(/BOM Name/i)
    const materialIdInput = screen.getByLabelText(/Material ID/i)
    const baseQuantityInput = screen.getByLabelText(/Base Quantity/i)
    const uomIdInput = screen.getByLabelText(/Unit of Measure ID/i)

    await user.clear(bomNumberInput)
    await user.type(bomNumberInput, 'BOM001')
    await user.clear(bomNameInput)
    await user.type(bomNameInput, 'Test BOM')
    await user.clear(materialIdInput)
    await user.type(materialIdInput, '1')
    await user.clear(baseQuantityInput)
    await user.type(baseQuantityInput, '1')
    await user.clear(uomIdInput)
    await user.type(uomIdInput, '1')

    const submitButton = screen.getByRole('button', { name: /Create BOM/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          bom_number: 'BOM001',
          bom_name: 'Test BOM',
          material_id: 1,
          base_quantity: 1,
          unit_of_measure_id: 1,
        })
      )
    })
  })

  it('should call onCancel when cancel button clicked', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(<BOMForm mode="create" onSubmit={onSubmit} onCancel={onCancel} />)

    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    await user.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
  })
})

describe('BOMForm - Edit Mode', () => {
  it('should render edit form with initial data', () => {
    const onSubmit = vi.fn()
    render(<BOMForm mode="edit" initialData={mockBOM} onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/BOM Number/i)).toHaveValue('BOM001')
    expect(screen.getByLabelText(/BOM Name/i)).toHaveValue('Test BOM')
    expect(screen.getByRole('button', { name: /Update BOM/i })).toBeInTheDocument()
  })

  it('should disable BOM number field in edit mode', () => {
    const onSubmit = vi.fn()
    render(<BOMForm mode="edit" initialData={mockBOM} onSubmit={onSubmit} />)

    const bomNumberInput = screen.getByLabelText(/BOM Number/i)
    expect(bomNumberInput).toBeDisabled()
  })

  it('should submit only changed fields in edit mode', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<BOMForm mode="edit" initialData={mockBOM} onSubmit={onSubmit} />)

    const bomNameInput = screen.getByLabelText(/BOM Name/i)
    await user.clear(bomNameInput)
    await user.type(bomNameInput, 'Updated BOM Name')

    const submitButton = screen.getByRole('button', { name: /Update BOM/i })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(onSubmit).toHaveBeenCalledWith({
          bom_name: 'Updated BOM Name',
        })
      },
      { timeout: 3000 }
    )
  })

  it('should display error message', () => {
    const onSubmit = vi.fn()
    render(<BOMForm mode="create" onSubmit={onSubmit} error="Test error message" />)

    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('should disable form when loading', () => {
    const onSubmit = vi.fn()
    render(<BOMForm mode="create" onSubmit={onSubmit} isLoading={true} />)

    expect(screen.getByLabelText(/BOM Number/i)).toBeDisabled()
    expect(screen.getByLabelText(/BOM Name/i)).toBeDisabled()
  })
})
