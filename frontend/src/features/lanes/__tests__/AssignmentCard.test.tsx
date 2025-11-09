/**
 * AssignmentCard Component Tests
 *
 * TDD RED Phase: Test assignment card display and interactions
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AssignmentCard } from '../components/AssignmentCard'
import type { LaneAssignment } from '../types/lane.types'

describe('AssignmentCard', () => {
  const mockAssignment: LaneAssignment = {
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
  }

  const mockOnClick = vi.fn()
  const startDate = new Date('2025-01-15')

  it('should render assignment details', () => {
    render(
      <AssignmentCard
        assignment={mockAssignment}
        onClick={mockOnClick}
        startDate={startDate}
        daysToShow={7}
      />
    )

    expect(screen.getByText(/WO-500/i)).toBeInTheDocument()
  })

  it('should handle click events', async () => {
    const user = userEvent.setup()

    render(
      <AssignmentCard
        assignment={mockAssignment}
        onClick={mockOnClick}
        startDate={startDate}
        daysToShow={7}
      />
    )

    const card = screen.getByRole('button')
    await user.click(card)
    expect(mockOnClick).toHaveBeenCalledWith(mockAssignment)
  })

  it('should apply status color coding', () => {
    const { container } = render(
      <AssignmentCard
        assignment={mockAssignment}
        onClick={mockOnClick}
        startDate={startDate}
        daysToShow={7}
      />
    )

    // PLANNED status should have blue styling
    const card = container.querySelector('.bg-blue-500')
    expect(card).toBeInTheDocument()
  })
})
