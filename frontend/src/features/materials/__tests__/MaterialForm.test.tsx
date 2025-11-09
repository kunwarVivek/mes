/**
 * MaterialForm Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MaterialForm } from '../components/MaterialForm'
import type { Material } from '../types/material.types'

const mockMaterial: Material = {
  id: 1,
  organization_id: 1,
  plant_id: 1,
  material_number: 'MAT001',
  material_name: 'Test Material',
  description: 'Test Description',
  material_category_id: 1,
  base_uom_id: 1,
  procurement_type: 'PURCHASE',
  mrp_type: 'MRP',
  safety_stock: 100,
  reorder_point: 50,
  lot_size: 10,
  lead_time_days: 5,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
}

describe('MaterialForm - Create Mode', () => {
  it('should render create form with empty fields', () => {
    const onSubmit = vi.fn()
    render(<MaterialForm mode="create" onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/Material Number/i)).toHaveValue('')
    expect(screen.getByLabelText(/Material Name/i)).toHaveValue('')
    expect(screen.getByRole('button', { name: /Create Material/i })).toBeInTheDocument()
  })

  it('should validate required fields', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<MaterialForm mode="create" onSubmit={onSubmit} />)

    const submitButton = screen.getByRole('button', { name: /Create Material/i })
    await user.click(submitButton)

    await waitFor(() => {
      // Zod validation shows format error for empty string
      expect(
        screen.getByText(/Material number must be uppercase alphanumeric only/i)
      ).toBeInTheDocument()
    })

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should validate material number format', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<MaterialForm mode="create" onSubmit={onSubmit} />)

    const materialNumberInput = screen.getByLabelText(/Material Number/i)
    await user.type(materialNumberInput, 'invalid-mat-123')

    const submitButton = screen.getByRole('button', { name: /Create Material/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(
        screen.getByText(/Material number must be uppercase alphanumeric only/i)
      ).toBeInTheDocument()
    })
  })

  it('should submit valid create form', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<MaterialForm mode="create" onSubmit={onSubmit} defaultOrgId={1} defaultPlantId={1} />)

    await user.type(screen.getByLabelText(/Material Number/i), 'MAT001')
    await user.type(screen.getByLabelText(/Material Name/i), 'Test Material')
    await user.type(screen.getByLabelText(/Material Category ID/i), '1')
    await user.type(screen.getByLabelText(/Base UOM ID/i), '1')

    const submitButton = screen.getByRole('button', { name: /Create Material/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          material_number: 'MAT001',
          material_name: 'Test Material',
          material_category_id: 1,
          base_uom_id: 1,
        })
      )
    })
  })

  it('should call onCancel when cancel button clicked', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(<MaterialForm mode="create" onSubmit={onSubmit} onCancel={onCancel} />)

    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    await user.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
  })
})

describe('MaterialForm - Edit Mode', () => {
  it('should render edit form with initial data', () => {
    const onSubmit = vi.fn()
    render(<MaterialForm mode="edit" initialData={mockMaterial} onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/Material Number/i)).toHaveValue('MAT001')
    expect(screen.getByLabelText(/Material Name/i)).toHaveValue('Test Material')
    expect(screen.getByRole('button', { name: /Update Material/i })).toBeInTheDocument()
  })

  it('should disable material number field in edit mode', () => {
    const onSubmit = vi.fn()
    render(<MaterialForm mode="edit" initialData={mockMaterial} onSubmit={onSubmit} />)

    const materialNumberInput = screen.getByLabelText(/Material Number/i)
    expect(materialNumberInput).toBeDisabled()
  })

  it('should submit only changed fields in edit mode', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<MaterialForm mode="edit" initialData={mockMaterial} onSubmit={onSubmit} />)

    const materialNameInput = screen.getByLabelText(/Material Name/i)
    await user.clear(materialNameInput)
    await user.type(materialNameInput, 'Updated Material Name')

    const submitButton = screen.getByRole('button', { name: /Update Material/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        material_name: 'Updated Material Name',
      })
    })
  })

  it('should display error message', () => {
    const onSubmit = vi.fn()
    render(<MaterialForm mode="create" onSubmit={onSubmit} error="Test error message" />)

    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('should disable form when loading', () => {
    const onSubmit = vi.fn()
    render(<MaterialForm mode="create" onSubmit={onSubmit} isLoading={true} />)

    expect(screen.getByLabelText(/Material Number/i)).toBeDisabled()
    expect(screen.getByLabelText(/Material Name/i)).toBeDisabled()
  })
})
