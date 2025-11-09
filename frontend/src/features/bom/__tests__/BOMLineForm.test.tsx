/**
 * BOMLineForm Component Tests
 *
 * TDD: RED phase - These tests will fail initially
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BOMLineForm } from '../components/BOMLineForm'
import type { BOMLineWithChildren } from '../types/bom.types'

const mockLine: BOMLineWithChildren = {
  id: 1,
  bom_header_id: 1,
  line_number: 10,
  component_material_id: 101,
  component_material_name: 'Frame',
  quantity: 1,
  unit_of_measure_id: 1,
  unit_of_measure: 'EA',
  scrap_factor: 5,
  is_phantom: false,
  backflush: false,
  created_at: '2024-01-01T00:00:00Z'
}

describe('BOMLineForm', () => {
  it('renders form with all fields', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(
      <BOMLineForm
        bomHeaderId={1}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    expect(screen.getByLabelText(/component material id/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/quantity/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/unit of measure/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/line number/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/scrap factor/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/phantom/i)).toBeInTheDocument()
  })

  it('shows "Add BOM Line" title when creating new line', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(
      <BOMLineForm
        bomHeaderId={1}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    expect(screen.getByText('Add BOM Line')).toBeInTheDocument()
  })

  it('shows "Edit BOM Line" title when editing existing line', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(
      <BOMLineForm
        bomHeaderId={1}
        line={mockLine}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    expect(screen.getByText('Edit BOM Line')).toBeInTheDocument()
  })

  it('shows parent context when adding child', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    const parentLine = { ...mockLine, component_material_name: 'Parent Assembly' }

    render(
      <BOMLineForm
        bomHeaderId={1}
        parentLine={parentLine}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    expect(screen.getByText(/Add Child to Parent Assembly/i)).toBeInTheDocument()
  })

  it('pre-fills form when editing existing line', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(
      <BOMLineForm
        bomHeaderId={1}
        line={mockLine}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    expect(screen.getByDisplayValue('101')).toBeInTheDocument() // material_id
    expect(screen.getByDisplayValue('1')).toBeInTheDocument() // quantity
    // Check the select has value="1" selected (EA)
    const select = screen.getByLabelText(/unit of measure/i) as HTMLSelectElement
    expect(select.value).toBe('1')
    expect(screen.getByDisplayValue('10')).toBeInTheDocument() // line_number
    expect(screen.getByDisplayValue('5')).toBeInTheDocument() // scrap_factor
  })

  it('submits form with correct data for new line', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(
      <BOMLineForm
        bomHeaderId={1}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    // Fill form
    await user.type(screen.getByLabelText(/component material id/i), '101')
    await user.type(screen.getByLabelText(/quantity/i), '2')
    await user.selectOptions(screen.getByLabelText(/unit of measure/i), '2') // KG has value="2"
    await user.type(screen.getByLabelText(/line number/i), '10')
    await user.type(screen.getByLabelText(/scrap factor/i), '3.5')
    await user.click(screen.getByLabelText(/phantom/i))

    // Submit
    await user.click(screen.getByRole('button', { name: /^add$/i }))

    expect(onSubmit).toHaveBeenCalledWith({
      bom_header_id: 1,
      component_material_id: 101,
      quantity: 2,
      unit_of_measure_id: 2, // KG
      line_number: 10,
      scrap_factor: 3.5,
      is_phantom: true,
      backflush: false
    })
  })

  it('submits form with correct data when editing', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(
      <BOMLineForm
        bomHeaderId={1}
        line={mockLine}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    // Change quantity
    const quantityInput = screen.getByLabelText(/quantity/i)
    await user.clear(quantityInput)
    await user.type(quantityInput, '5')

    // Submit
    await user.click(screen.getByRole('button', { name: /update/i }))

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        quantity: 5
      })
    )
  })

  it('calls onCancel when cancel button clicked', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(
      <BOMLineForm
        bomHeaderId={1}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    await user.click(screen.getByRole('button', { name: /cancel/i }))

    expect(onCancel).toHaveBeenCalled()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('validates required fields', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(
      <BOMLineForm
        bomHeaderId={1}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    // Try to submit without filling required fields
    await user.click(screen.getByRole('button', { name: /add/i }))

    // Form should not submit
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('defaults scrap factor to 0', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(
      <BOMLineForm
        bomHeaderId={1}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    expect(screen.getByLabelText(/scrap factor/i)).toHaveValue(0)
  })

  it('defaults is_phantom to false', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(
      <BOMLineForm
        bomHeaderId={1}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    expect(screen.getByLabelText(/phantom/i)).not.toBeChecked()
  })

  it('shows unit of measure options', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(
      <BOMLineForm
        bomHeaderId={1}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    )

    const select = screen.getByLabelText(/unit of measure/i)
    expect(select).toBeInTheDocument()

    // Check for common UOM options
    expect(screen.getByRole('option', { name: /each/i })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /kilogram/i })).toBeInTheDocument()
  })
})
