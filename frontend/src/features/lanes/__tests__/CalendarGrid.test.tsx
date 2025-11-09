/**
 * CalendarGrid Component Tests
 *
 * TDD RED Phase: Test calendar grid rendering and interactions
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CalendarGrid } from '../components/CalendarGrid'
import type { Lane, LaneAssignment } from '../types/lane.types'

describe('CalendarGrid', () => {
  const mockLanes: Lane[] = [
    {
      id: 1,
      plant_id: 100,
      lane_code: 'L001',
      lane_name: 'Assembly Line 1',
      capacity_per_day: '1000',
      is_active: true,
      created_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 2,
      plant_id: 100,
      lane_code: 'L002',
      lane_name: 'Assembly Line 2',
      capacity_per_day: '800',
      is_active: true,
      created_at: '2025-01-01T00:00:00Z',
    },
  ]

  const _mockAssignments: LaneAssignment[] = [
    {
      id: 1,
      organization_id: 1,
      plant_id: 100,
      lane_id: 1,
      work_order_id: 500,
      scheduled_start: '2025-01-15',
      scheduled_end: '2025-01-17',
      allocated_capacity: '800',
      priority: 1,
      status: 'PLANNED' as const,
      created_at: '2025-01-01T00:00:00Z',
    },
  ]

  const mockOnDateChange = vi.fn()
  const mockOnCellClick = vi.fn()
  const startDate = new Date('2025-01-15')

  it('should render calendar grid with lanes', () => {
    render(
      <CalendarGrid
        lanes={mockLanes}
        assignments={[]}
        startDate={startDate}
        daysToShow={7}
        onDateChange={mockOnDateChange}
        onCellClick={mockOnCellClick}
        isLoading={false}
      />
    )

    expect(screen.getByText('Assembly Line 1')).toBeInTheDocument()
    expect(screen.getByText('Assembly Line 2')).toBeInTheDocument()
  })

  it('should render date headers for 7 days', () => {
    render(
      <CalendarGrid
        lanes={mockLanes}
        assignments={[]}
        startDate={startDate}
        daysToShow={7}
        onDateChange={mockOnDateChange}
        onCellClick={mockOnCellClick}
        isLoading={false}
      />
    )

    // Should display dates from Jan 15 to Jan 21
    expect(screen.getAllByText(/Jan 15/).length).toBeGreaterThan(0)
  })

  it('should handle cell click', async () => {
    const user = userEvent.setup()

    render(
      <CalendarGrid
        lanes={mockLanes}
        assignments={[]}
        startDate={startDate}
        daysToShow={7}
        onDateChange={mockOnDateChange}
        onCellClick={mockOnCellClick}
        isLoading={false}
      />
    )

    const cells = screen.getAllByRole('button', { name: /cell/i })
    if (cells.length > 0) {
      await user.click(cells[0])
      expect(mockOnCellClick).toHaveBeenCalled()
    }
  })

  it('should show loading state', () => {
    render(
      <CalendarGrid
        lanes={mockLanes}
        assignments={[]}
        startDate={startDate}
        daysToShow={7}
        onDateChange={mockOnDateChange}
        onCellClick={mockOnCellClick}
        isLoading={true}
      />
    )

    expect(screen.getAllByText(/loading/i).length).toBeGreaterThan(0)
  })

  it('should handle navigation buttons', async () => {
    const user = userEvent.setup()

    render(
      <CalendarGrid
        lanes={mockLanes}
        assignments={[]}
        startDate={startDate}
        daysToShow={7}
        onDateChange={mockOnDateChange}
        onCellClick={mockOnCellClick}
        isLoading={false}
      />
    )

    const prevButton = screen.getByRole('button', { name: /previous/i })
    await user.click(prevButton)
    expect(mockOnDateChange).toHaveBeenCalled()

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)
    expect(mockOnDateChange).toHaveBeenCalled()
  })

  it('should display lane capacity', () => {
    render(
      <CalendarGrid
        lanes={mockLanes}
        assignments={[]}
        startDate={startDate}
        daysToShow={7}
        onDateChange={mockOnDateChange}
        onCellClick={mockOnCellClick}
        isLoading={false}
      />
    )

    expect(screen.getByText(/1000/)).toBeInTheDocument() // L001 capacity
    expect(screen.getByText(/800/)).toBeInTheDocument() // L002 capacity
  })
})
