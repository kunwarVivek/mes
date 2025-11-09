/**
 * MachineForm Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MachineForm } from '../components/MachineForm'
import type { Machine, CreateMachineDTO } from '../types/machine.types'

const mockMachine: Machine = {
  id: 1,
  organization_id: 1,
  plant_id: 1,
  machine_code: 'CNC001',
  machine_name: 'CNC Machine 1',
  description: 'High-precision CNC',
  work_center_id: 1,
  status: 'AVAILABLE',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
}

describe('MachineForm', () => {
  it('should render empty form for creation', () => {
    render(<MachineForm onSubmit={vi.fn()} />)

    expect(screen.getByLabelText(/machine code/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/machine name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/status/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
  })

  it('should render form with initial values for edit', () => {
    render(<MachineForm initialData={mockMachine} onSubmit={vi.fn()} />)

    expect(screen.getByDisplayValue('CNC001')).toBeInTheDocument()
    expect(screen.getByDisplayValue('CNC Machine 1')).toBeInTheDocument()
    expect(screen.getByDisplayValue('High-precision CNC')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /update/i })).toBeInTheDocument()
  })

  it('should validate required fields', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<MachineForm onSubmit={onSubmit} />)

    const submitButton = screen.getByRole('button', { name: /create/i })
    await user.click(submitButton)

    await waitFor(() => {
      // Check for validation errors - they appear as "must be uppercase alphanumeric only" for empty string
      const errors = screen.getAllByText(/machine code|machine name/i)
      expect(errors.length).toBeGreaterThan(0)
    })

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should validate machine code format', async () => {
    const user = userEvent.setup()

    render(<MachineForm onSubmit={vi.fn()} />)

    const codeInput = screen.getByLabelText(/machine code/i)
    await user.type(codeInput, 'invalid-code')

    const submitButton = screen.getByRole('button', { name: /create/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/must be uppercase alphanumeric only/i)).toBeInTheDocument()
    })
  })

  it('should validate machine code length', async () => {
    const user = userEvent.setup()

    render(<MachineForm onSubmit={vi.fn()} />)

    const codeInput = screen.getByLabelText(/machine code/i)
    await user.type(codeInput, 'A'.repeat(21)) // 21 characters (max is 20)

    const submitButton = screen.getByRole('button', { name: /create/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/must be at most 20 characters/i)).toBeInTheDocument()
    })
  })

  it('should submit valid form data', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()

    render(<MachineForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/machine code/i), 'CNC002')
    await user.type(screen.getByLabelText(/machine name/i), 'New CNC Machine')
    await user.type(screen.getByLabelText(/description/i), 'Description here')

    // Select status
    const statusSelect = screen.getByLabelText(/status/i)
    await user.selectOptions(statusSelect, 'AVAILABLE')

    const submitButton = screen.getByRole('button', { name: /create/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled()
    })
  })

  it('should call onCancel when cancel button clicked', async () => {
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(<MachineForm onSubmit={vi.fn()} onCancel={onCancel} />)

    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
  })

  it('should disable submit button when submitting', () => {
    render(<MachineForm onSubmit={vi.fn()} isSubmitting={true} />)

    const submitButton = screen.getByRole('button', { name: /create/i })
    expect(submitButton).toBeDisabled()
  })

  it('should display all status options', () => {
    render(<MachineForm onSubmit={vi.fn()} />)

    const statusSelect = screen.getByLabelText(/status/i)
    const options = Array.from(statusSelect.querySelectorAll('option'))

    expect(options.map(o => o.textContent)).toContain('AVAILABLE')
    expect(options.map(o => o.textContent)).toContain('RUNNING')
    expect(options.map(o => o.textContent)).toContain('IDLE')
    expect(options.map(o => o.textContent)).toContain('DOWN')
    expect(options.map(o => o.textContent)).toContain('SETUP')
    expect(options.map(o => o.textContent)).toContain('MAINTENANCE')
  })

  it('should show error message when provided', () => {
    const errorMessage = 'Failed to create machine'
    render(<MachineForm onSubmit={vi.fn()} error={errorMessage} />)

    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })

  it('should validate description length', async () => {
    const user = userEvent.setup()

    render(<MachineForm onSubmit={vi.fn()} />)

    const descInput = screen.getByLabelText(/description/i)
    await user.type(descInput, 'A'.repeat(501)) // 501 characters (max is 500)

    const submitButton = screen.getByRole('button', { name: /create/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/must be at most 500 characters/i)).toBeInTheDocument()
    })
  })
})
