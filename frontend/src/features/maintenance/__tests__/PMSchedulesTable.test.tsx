/**
 * PMSchedulesTable Component Tests
 *
 * TDD: Testing PM schedules table display and interactions
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PMSchedulesTable } from '../components/PMSchedulesTable'
import type { PMSchedule } from '../types/maintenance.types'

describe('PMSchedulesTable', () => {
  const mockSchedules: PMSchedule[] = [
    {
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
    },
    {
      id: 2,
      organization_id: 1,
      plant_id: 1,
      schedule_code: 'PM002',
      schedule_name: 'Quarterly Inspection',
      machine_id: 10,
      trigger_type: 'METER',
      frequency_days: null,
      meter_threshold: 1000,
      is_active: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ]

  it('should render table headers correctly', () => {
    render(<PMSchedulesTable schedules={mockSchedules} isLoading={false} />)

    expect(screen.getByText('Schedule Code')).toBeInTheDocument()
    expect(screen.getByText('Schedule Name')).toBeInTheDocument()
    expect(screen.getByText('Machine')).toBeInTheDocument()
    expect(screen.getByText('Trigger Type')).toBeInTheDocument()
    expect(screen.getByText('Frequency')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Actions')).toBeInTheDocument()
  })

  it('should render schedule data correctly', () => {
    render(<PMSchedulesTable schedules={mockSchedules} isLoading={false} />)

    expect(screen.getByText('PM001')).toBeInTheDocument()
    expect(screen.getByText('Monthly Lubrication')).toBeInTheDocument()
    expect(screen.getByText('PM002')).toBeInTheDocument()
    expect(screen.getByText('Quarterly Inspection')).toBeInTheDocument()
  })

  it('should display CALENDAR trigger type with frequency days', () => {
    render(<PMSchedulesTable schedules={mockSchedules} isLoading={false} />)

    expect(screen.getByText('CALENDAR')).toBeInTheDocument()
    expect(screen.getByText('30 days')).toBeInTheDocument()
  })

  it('should display METER trigger type with threshold', () => {
    render(<PMSchedulesTable schedules={mockSchedules} isLoading={false} />)

    expect(screen.getByText('METER')).toBeInTheDocument()
    expect(screen.getByText('1000 units')).toBeInTheDocument()
  })

  it('should display active status badge', () => {
    render(<PMSchedulesTable schedules={mockSchedules} isLoading={false} />)

    const activeBadges = screen.getAllByText('Active')
    expect(activeBadges.length).toBeGreaterThan(0)
  })

  it('should display inactive status badge', () => {
    render(<PMSchedulesTable schedules={mockSchedules} isLoading={false} />)

    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })

  it('should render action buttons for each schedule', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()

    render(
      <PMSchedulesTable
        schedules={mockSchedules}
        isLoading={false}
        onEdit={onEdit}
        onDelete={onDelete}
      />
    )

    const editButtons = screen.getAllByRole('button', { name: /edit/i })
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })

    expect(editButtons).toHaveLength(2)
    expect(deleteButtons).toHaveLength(2)
  })

  it('should call onEdit when edit button is clicked', () => {
    const onEdit = vi.fn()

    render(
      <PMSchedulesTable schedules={mockSchedules} isLoading={false} onEdit={onEdit} />
    )

    const editButtons = screen.getAllByRole('button', { name: /edit/i })
    editButtons[0].click()

    expect(onEdit).toHaveBeenCalledWith(mockSchedules[0])
  })

  it('should call onDelete when delete button is clicked', () => {
    const onDelete = vi.fn()

    render(
      <PMSchedulesTable schedules={mockSchedules} isLoading={false} onDelete={onDelete} />
    )

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    deleteButtons[0].click()

    expect(onDelete).toHaveBeenCalledWith(mockSchedules[0])
  })

  it('should show loading state', () => {
    render(<PMSchedulesTable schedules={[]} isLoading={true} />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('should show empty state when no schedules', () => {
    render(<PMSchedulesTable schedules={[]} isLoading={false} />)

    expect(screen.getByText(/no pm schedules found/i)).toBeInTheDocument()
  })

  it('should filter schedules by search term', () => {
    render(
      <PMSchedulesTable
        schedules={mockSchedules}
        isLoading={false}
        searchTerm="lubrication"
      />
    )

    expect(screen.getByText('Monthly Lubrication')).toBeInTheDocument()
    expect(screen.queryByText('Quarterly Inspection')).not.toBeInTheDocument()
  })
})
