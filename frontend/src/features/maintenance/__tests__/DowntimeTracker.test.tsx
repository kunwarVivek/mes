/**
 * DowntimeTracker Component Tests
 *
 * TDD: Testing downtime event tracking and display
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DowntimeTracker } from '../components/DowntimeTracker'
import type { DowntimeEvent } from '../types/maintenance.types'

describe('DowntimeTracker', () => {
  const mockEvents: DowntimeEvent[] = [
    {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      machine_id: 10,
      category: 'BREAKDOWN',
      reason: 'Belt failure',
      started_at: '2024-01-01T08:00:00Z',
      ended_at: '2024-01-01T10:30:00Z',
      duration_minutes: 150,
      notes: 'Replaced belt',
      created_at: '2024-01-01T08:00:00Z',
    },
    {
      id: 2,
      organization_id: 1,
      plant_id: 1,
      machine_id: 10,
      category: 'PLANNED_MAINTENANCE',
      reason: 'Scheduled PM',
      started_at: '2024-01-02T14:00:00Z',
      ended_at: null,
      duration_minutes: null,
      notes: null,
      created_at: '2024-01-02T14:00:00Z',
    },
  ]

  it('should render downtime events list', () => {
    render(<DowntimeTracker events={mockEvents} machineId={10} />)

    expect(screen.getByText('Belt failure')).toBeInTheDocument()
    expect(screen.getByText('Scheduled PM')).toBeInTheDocument()
  })

  it('should display category badges with correct colors', () => {
    render(<DowntimeTracker events={mockEvents} machineId={10} />)

    expect(screen.getByText('BREAKDOWN')).toBeInTheDocument()
    expect(screen.getByText('PLANNED_MAINTENANCE')).toBeInTheDocument()
  })

  it('should display duration for completed events', () => {
    render(<DowntimeTracker events={mockEvents} machineId={10} />)

    expect(screen.getByText('150 min')).toBeInTheDocument()
  })

  it('should display "Ongoing" for events without end time', () => {
    render(<DowntimeTracker events={mockEvents} machineId={10} />)

    expect(screen.getByText('Ongoing')).toBeInTheDocument()
  })

  it('should show "Log Downtime" button', () => {
    render(<DowntimeTracker events={mockEvents} machineId={10} />)

    expect(screen.getByRole('button', { name: /log downtime/i })).toBeInTheDocument()
  })

  it('should open downtime form when "Log Downtime" clicked', async () => {
    const user = userEvent.setup()

    render(<DowntimeTracker events={mockEvents} machineId={10} />)

    const logButton = screen.getByRole('button', { name: /log downtime/i })
    await user.click(logButton)

    // Check that form fields appear (there will be multiple category selects, so we just check count)
    const categorySelects = screen.getAllByRole('combobox')
    expect(categorySelects.length).toBeGreaterThan(0)
    expect(screen.getByLabelText(/reason/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/started at/i)).toBeInTheDocument()
  })

  it('should validate downtime form fields', async () => {
    const user = userEvent.setup()
    const onCreate = vi.fn()

    render(<DowntimeTracker events={mockEvents} machineId={10} onCreate={onCreate} />)

    const logButton = screen.getByRole('button', { name: /log downtime/i })
    await user.click(logButton)

    const submitButton = screen.getByRole('button', { name: /submit/i })
    await user.click(submitButton)

    // Form validation prevents submission
    expect(onCreate).not.toHaveBeenCalled()
  })

  it('should submit new downtime event', async () => {
    const user = userEvent.setup()
    const onCreate = vi.fn()

    render(<DowntimeTracker events={mockEvents} machineId={10} onCreate={onCreate} />)

    const logButton = screen.getByRole('button', { name: /log downtime/i })
    await user.click(logButton)

    // Find the category select in the form (id="category")
    const categorySelect = screen.getByRole('combobox', { name: 'Category *' })
    await user.selectOptions(categorySelect, 'BREAKDOWN')
    await user.type(screen.getByLabelText(/reason/i), 'Motor overheating')
    await user.type(screen.getByLabelText(/started at/i), '2024-01-03T10:00')

    const submitButton = screen.getByRole('button', { name: /submit/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onCreate).toHaveBeenCalled()
      const callArgs = onCreate.mock.calls[0][0]
      expect(callArgs.machine_id).toBe(10)
      expect(callArgs.category).toBe('BREAKDOWN')
      expect(callArgs.reason).toBe('Motor overheating')
    })
  })

  it('should allow ending an ongoing downtime event', async () => {
    const user = userEvent.setup()
    const onEnd = vi.fn()

    render(<DowntimeTracker events={mockEvents} machineId={10} onEnd={onEnd} />)

    // Click the End button for the ongoing event
    const endButtons = screen.getAllByRole('button', { name: /end/i })
    await user.click(endButtons[0])

    // Verify the end form appears
    expect(screen.getByLabelText(/ended at/i)).toBeInTheDocument()

    // Fill in end time
    await user.type(screen.getByLabelText(/ended at/i), '2024-01-02T16:00')

    // Submit the form
    const confirmButton = screen.getByRole('button', { name: /confirm/i })
    await user.click(confirmButton)

    // Verify onEnd was called with the correct event ID and data
    await waitFor(
      () => {
        expect(onEnd).toHaveBeenCalled()
      },
      { timeout: 2000 }
    )

    if (onEnd.mock.calls.length > 0) {
      const firstArg = onEnd.mock.calls[0][0]
      const secondArg = onEnd.mock.calls[0][1]
      expect(firstArg).toBe(2)
      expect(secondArg.ended_at).toBeDefined()
    }
  })

  it('should validate end time is after start time', async () => {
    const user = userEvent.setup()
    const onEnd = vi.fn()

    // Only event 2 is ongoing (no ended_at)
    render(<DowntimeTracker events={mockEvents} machineId={10} onEnd={onEnd} />)

    // Click end button for the ongoing event
    const endButtons = screen.getAllByRole('button', { name: /end/i })
    expect(endButtons.length).toBeGreaterThan(0)
    await user.click(endButtons[0])

    // Try to set end time before start time
    await user.type(screen.getByLabelText(/ended at/i), '2024-01-02T10:00')

    const confirmButton = screen.getByRole('button', { name: /confirm/i })
    await user.click(confirmButton)

    // Validation should prevent the call
    expect(onEnd).not.toHaveBeenCalled()
  })

  it('should display MTBF/MTTR metrics', () => {
    const metrics = {
      machine_id: 10,
      time_period_start: '2024-01-01T00:00:00Z',
      time_period_end: '2024-01-31T23:59:59Z',
      total_operating_time: 42000,
      total_repair_time: 720,
      number_of_failures: 3,
      mtbf: 14000,
      mttr: 240,
      availability: 0.983,
    }

    render(<DowntimeTracker events={mockEvents} machineId={10} metrics={metrics} />)

    // Use getAllByText for labels that appear multiple times
    const mtbfElements = screen.getAllByText(/mtbf/i)
    expect(mtbfElements.length).toBeGreaterThan(0)
    expect(screen.getByText('14000 min')).toBeInTheDocument()

    const mttrElements = screen.getAllByText(/mttr/i)
    expect(mttrElements.length).toBeGreaterThan(0)
    expect(screen.getByText('240 min')).toBeInTheDocument()

    const availElements = screen.getAllByText(/availability/i)
    expect(availElements.length).toBeGreaterThan(0)
    expect(screen.getByText('98.3%')).toBeInTheDocument()
  })

  it('should show empty state when no events', () => {
    render(<DowntimeTracker events={[]} machineId={10} />)

    expect(screen.getByText(/no downtime events recorded/i)).toBeInTheDocument()
  })

  it('should filter events by category', async () => {
    const user = userEvent.setup()

    render(<DowntimeTracker events={mockEvents} machineId={10} />)

    const categoryFilter = screen.getByLabelText(/filter by category/i)
    await user.selectOptions(categoryFilter, 'BREAKDOWN')

    expect(screen.getByText('Belt failure')).toBeInTheDocument()
    expect(screen.queryByText('Scheduled PM')).not.toBeInTheDocument()
  })

  it('should filter events by date range', async () => {
    const user = userEvent.setup()

    render(<DowntimeTracker events={mockEvents} machineId={10} />)

    // Filter to only show Jan 1st events
    await user.type(screen.getByLabelText(/start date/i), '2024-01-01')
    await user.type(screen.getByLabelText(/end date/i), '2024-01-01')

    // Event 1 started on Jan 1st, should be visible
    const beltFailureElements = screen.queryAllByText('Belt failure')
    expect(beltFailureElements.length).toBeGreaterThan(0)

    // Event 2 started on Jan 2nd, should not be visible
    expect(screen.queryByText('Scheduled PM')).not.toBeInTheDocument()
  })
})
