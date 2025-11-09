/**
 * PMScheduleForm Component Tests
 *
 * TDD: Testing PM schedule form validation and submission
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PMScheduleForm } from '../components/PMScheduleForm'
import type { PMSchedule } from '../types/maintenance.types'

describe('PMScheduleForm', () => {
  const mockMachines = [
    { id: 10, name: 'CNC Machine 1' },
    { id: 11, name: 'Lathe Machine 2' },
  ]

  describe('Create Mode', () => {
    it('should render all form fields for creation', () => {
      render(<PMScheduleForm machines={mockMachines} onSubmit={vi.fn()} />)

      expect(screen.getByLabelText(/schedule code/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/schedule name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/machine/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/trigger type/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
    })

    it('should validate required fields', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()

      render(<PMScheduleForm machines={mockMachines} onSubmit={onSubmit} />)

      const submitButton = screen.getByRole('button', { name: /create/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/schedule code is required/i)).toBeInTheDocument()
        expect(screen.getByText(/schedule name is required/i)).toBeInTheDocument()
      })

      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('should validate schedule code format (uppercase alphanumeric)', async () => {
      const user = userEvent.setup()

      render(<PMScheduleForm machines={mockMachines} onSubmit={vi.fn()} />)

      const codeInput = screen.getByLabelText(/schedule code/i)
      await user.type(codeInput, 'pm-001')

      const submitButton = screen.getByRole('button', { name: /create/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(
          screen.getByText(/schedule code must be uppercase alphanumeric/i)
        ).toBeInTheDocument()
      })
    })

    it('should show frequency_days field when CALENDAR trigger type selected', async () => {
      const user = userEvent.setup()

      render(<PMScheduleForm machines={mockMachines} onSubmit={vi.fn()} />)

      const triggerTypeSelect = screen.getByLabelText(/trigger type/i)
      await user.selectOptions(triggerTypeSelect, 'CALENDAR')

      expect(screen.getByLabelText(/frequency \(days\)/i)).toBeInTheDocument()
      expect(screen.queryByLabelText(/meter threshold/i)).not.toBeInTheDocument()
    })

    it('should show meter_threshold field when METER trigger type selected', async () => {
      const user = userEvent.setup()

      render(<PMScheduleForm machines={mockMachines} onSubmit={vi.fn()} />)

      const triggerTypeSelect = screen.getByLabelText(/trigger type/i)
      await user.selectOptions(triggerTypeSelect, 'METER')

      expect(screen.getByLabelText(/meter threshold/i)).toBeInTheDocument()
      expect(screen.queryByLabelText(/frequency \(days\)/i)).not.toBeInTheDocument()
    })

    it('should submit valid form data', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()

      render(<PMScheduleForm machines={mockMachines} onSubmit={onSubmit} />)

      await user.type(screen.getByLabelText(/schedule code/i), 'PM001')
      await user.type(screen.getByLabelText(/schedule name/i), 'Monthly Lubrication')
      await user.selectOptions(screen.getByLabelText(/machine/i), '10')
      await user.selectOptions(screen.getByLabelText(/trigger type/i), 'CALENDAR')
      await user.type(screen.getByLabelText(/frequency \(days\)/i), '30')

      const submitButton = screen.getByRole('button', { name: /create/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled()
        const callArgs = onSubmit.mock.calls[0][0]
        expect(callArgs.schedule_code).toBe('PM001')
        expect(callArgs.schedule_name).toBe('Monthly Lubrication')
        expect(callArgs.machine_id).toBe(10)
        expect(callArgs.trigger_type).toBe('CALENDAR')
        expect(callArgs.frequency_days).toBe(30)
        expect(callArgs.is_active).toBe(true)
      })
    })
  })

  describe('Edit Mode', () => {
    const existingSchedule: PMSchedule = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      schedule_code: 'PM001',
      schedule_name: 'Monthly Lubrication',
      machine_id: 10,
      trigger_type: 'CALENDAR',
      frequency_days: 30,
      meter_threshold: null,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    it('should pre-fill form with existing schedule data', () => {
      render(
        <PMScheduleForm
          machines={mockMachines}
          schedule={existingSchedule}
          onSubmit={vi.fn()}
        />
      )

      expect(screen.getByDisplayValue('PM001')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Monthly Lubrication')).toBeInTheDocument()
      expect(screen.getByDisplayValue('30')).toBeInTheDocument()
    })

    it('should show update button in edit mode', () => {
      render(
        <PMScheduleForm
          machines={mockMachines}
          schedule={existingSchedule}
          onSubmit={vi.fn()}
        />
      )

      expect(screen.getByRole('button', { name: /update/i })).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /create/i })).not.toBeInTheDocument()
    })

    it('should disable schedule code field in edit mode', () => {
      render(
        <PMScheduleForm
          machines={mockMachines}
          schedule={existingSchedule}
          onSubmit={vi.fn()}
        />
      )

      const codeInput = screen.getByLabelText(/schedule code/i)
      expect(codeInput).toBeDisabled()
    })

    it('should submit updated data', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()

      render(
        <PMScheduleForm
          machines={mockMachines}
          schedule={existingSchedule}
          onSubmit={onSubmit}
        />
      )

      const nameInput = screen.getByLabelText(/schedule name/i)
      await user.clear(nameInput)
      await user.type(nameInput, 'Weekly Lubrication')

      const frequencyInput = screen.getByLabelText(/frequency \(days\)/i)
      await user.clear(frequencyInput)
      await user.type(frequencyInput, '7')

      const submitButton = screen.getByRole('button', { name: /update/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled()
        const callArgs = onSubmit.mock.calls[0][0]
        expect(callArgs.schedule_name).toBe('Weekly Lubrication')
        expect(callArgs.frequency_days).toBe(7)
        expect(callArgs.is_active).toBe(true)
      })
    })
  })

  it('should show cancel button and call onCancel', async () => {
    const user = userEvent.setup()
    const onCancel = vi.fn()

    render(
      <PMScheduleForm machines={mockMachines} onSubmit={vi.fn()} onCancel={onCancel} />
    )

    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
  })

  it('should toggle is_active checkbox', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(<PMScheduleForm machines={mockMachines} onSubmit={onSubmit} />)

    const activeCheckbox = screen.getByLabelText(/active/i)
    expect(activeCheckbox).toBeChecked()

    await user.click(activeCheckbox)
    expect(activeCheckbox).not.toBeChecked()
  })
})
