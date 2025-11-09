/**
 * NCRForm Component Tests
 *
 * TDD: Testing form rendering, validation, and submission
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NCRForm } from '../components/NCRForm'

describe('NCRForm', () => {
  it('should render form with all fields', () => {
    const onSubmit = vi.fn()
    render(<NCRForm onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/NCR Number/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Work Order ID/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Material ID/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Defect Type/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Defect Description/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Quantity Defective/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create NCR/i })).toBeInTheDocument()
  })

  it('should render cancel button when onCancel is provided', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    render(<NCRForm onSubmit={onSubmit} onCancel={onCancel} />)

    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument()
  })

  it('should populate form with default values', () => {
    const onSubmit = vi.fn()
    render(
      <NCRForm
        onSubmit={onSubmit}
        defaultWorkOrderId={100}
        defaultMaterialId={50}
        defaultReporterId={5}
      />
    )

    expect(screen.getByLabelText(/Work Order ID/i)).toHaveValue(100)
    expect(screen.getByLabelText(/Material ID/i)).toHaveValue(50)
  })

  it('should prevent submission when NCR number is empty', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<NCRForm onSubmit={onSubmit} />)

    const submitButton = screen.getByRole('button', { name: /Create NCR/i })
    await user.click(submitButton)

    // Validation should prevent submission
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should show validation error when description is too short', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<NCRForm onSubmit={onSubmit} defaultWorkOrderId={100} defaultMaterialId={50} />)

    const ncrNumber = screen.getByLabelText(/NCR Number/i)
    const description = screen.getByLabelText(/Defect Description/i)
    const quantity = screen.getByLabelText(/Quantity Defective/i)

    await user.type(ncrNumber, 'NCR-001')
    await user.type(description, 'Short')
    await user.clear(quantity)
    await user.type(quantity, '5')

    const submitButton = screen.getByRole('button', { name: /Create NCR/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(
        screen.getByText(/Description must be at least 10 characters/i)
      ).toBeInTheDocument()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should show character count for description', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<NCRForm onSubmit={onSubmit} />)

    const description = screen.getByLabelText(/Defect Description/i)
    await user.type(description, 'This is a test description')

    expect(screen.getByText(/26 \/ 500 characters/i)).toBeInTheDocument()
  })

  it('should submit form with valid data', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(
      <NCRForm
        onSubmit={onSubmit}
        defaultWorkOrderId={100}
        defaultMaterialId={50}
        defaultReporterId={1}
      />
    )

    const ncrNumber = screen.getByLabelText(/NCR Number/i)
    const description = screen.getByLabelText(/Defect Description/i)
    const quantity = screen.getByLabelText(/Quantity Defective/i)
    const defectType = screen.getByLabelText(/Defect Type/i)

    await user.type(ncrNumber, 'NCR-2024-001')
    await user.type(description, 'Part dimension out of tolerance by 0.5mm')
    await user.clear(quantity)
    await user.type(quantity, '5')
    await user.selectOptions(defectType, 'DIMENSIONAL')

    const submitButton = screen.getByRole('button', { name: /Create NCR/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        ncr_number: 'NCR-2024-001',
        work_order_id: 100,
        material_id: 50,
        defect_type: 'DIMENSIONAL',
        defect_description: 'Part dimension out of tolerance by 0.5mm',
        quantity_defective: 5,
        reported_by_user_id: 1,
        attachment_urls: [],
      })
    })
  })

  it('should show error message when submission fails', () => {
    const onSubmit = vi.fn()
    render(<NCRForm onSubmit={onSubmit} error="Failed to create NCR" />)

    expect(screen.getByRole('alert')).toHaveTextContent('Failed to create NCR')
  })

  it('should disable form when isLoading is true', () => {
    const onSubmit = vi.fn()
    render(<NCRForm onSubmit={onSubmit} isLoading={true} />)

    expect(screen.getByLabelText(/NCR Number/i)).toBeDisabled()
    expect(screen.getByLabelText(/Work Order ID/i)).toBeDisabled()
    expect(screen.getByLabelText(/Material ID/i)).toBeDisabled()
    expect(screen.getByLabelText(/Defect Type/i)).toBeDisabled()
    expect(screen.getByLabelText(/Defect Description/i)).toBeDisabled()
    expect(screen.getByLabelText(/Quantity Defective/i)).toBeDisabled()
  })

  it('should call onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    const onCancel = vi.fn()
    render(<NCRForm onSubmit={onSubmit} onCancel={onCancel} />)

    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    await user.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
  })

  it('should allow submission after fixing validation errors', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<NCRForm onSubmit={onSubmit} />)

    // First submit with invalid data
    const submitButton = screen.getByRole('button', { name: /Create NCR/i })
    await user.click(submitButton)
    expect(onSubmit).not.toHaveBeenCalled()

    // Fix all fields
    const ncrNumber = screen.getByLabelText(/NCR Number/i)
    const workOrderId = screen.getByLabelText(/Work Order ID/i)
    const materialId = screen.getByLabelText(/Material ID/i)
    const description = screen.getByLabelText(/Defect Description/i)
    const quantity = screen.getByLabelText(/Quantity Defective/i)

    await user.type(ncrNumber, 'NCR-001')
    await user.clear(workOrderId)
    await user.type(workOrderId, '100')
    await user.clear(materialId)
    await user.type(materialId, '50')
    await user.type(description, 'Valid description here')
    await user.clear(quantity)
    await user.type(quantity, '5')

    // Now submission should work
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled()
    })
  })

  it('should prevent submission when work_order_id is zero', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<NCRForm onSubmit={onSubmit} />)

    const ncrNumber = screen.getByLabelText(/NCR Number/i)
    const materialId = screen.getByLabelText(/Material ID/i)
    const description = screen.getByLabelText(/Defect Description/i)
    const quantity = screen.getByLabelText(/Quantity Defective/i)

    // Fill in all fields except leave work_order_id as 0 (default)
    await user.type(ncrNumber, 'NCR-001')
    await user.clear(materialId)
    await user.type(materialId, '50')
    await user.type(description, 'Test description here')
    await user.clear(quantity)
    await user.type(quantity, '5')

    const submitButton = screen.getByRole('button', { name: /Create NCR/i })
    await user.click(submitButton)

    // Validation should prevent submission (work_order_id must be positive, not 0)
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should render all defect type options', () => {
    const onSubmit = vi.fn()
    render(<NCRForm onSubmit={onSubmit} />)

    const defectType = screen.getByLabelText(/Defect Type/i)
    const options = Array.from(defectType.querySelectorAll('option'))

    expect(options).toHaveLength(5)
    expect(options.map((opt) => opt.value)).toEqual([
      'DIMENSIONAL',
      'VISUAL',
      'FUNCTIONAL',
      'MATERIAL',
      'OTHER',
    ])
  })
})
