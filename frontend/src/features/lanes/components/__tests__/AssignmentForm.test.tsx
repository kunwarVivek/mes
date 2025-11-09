/**
 * AssignmentForm Component Tests
 *
 * TDD: Comprehensive tests for lane assignment form validation and submission
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AssignmentForm } from '../AssignmentForm'
import type { LaneAssignment } from '../../types/lane.types'
import { useAuthStore } from '@/stores/auth.store'

// Mock auth store
vi.mock('@/stores/auth.store', () => ({
  useAuthStore: vi.fn(),
}))

describe('AssignmentForm', () => {
  const mockOnSubmit = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    // Setup default auth store mock
    vi.mocked(useAuthStore).mockReturnValue({
      currentOrg: { id: 1, organization_code: 'ORG001', organization_name: 'Test Org' },
      currentPlant: { id: 100, plant_code: 'P001', plant_name: 'Test Plant' },
    } as any)
  })

  const mockAssignment: LaneAssignment = {
    id: 1,
    organization_id: 1,
    plant_id: 100,
    lane_id: 5,
    work_order_id: 500,
    scheduled_start: '2025-01-15',
    scheduled_end: '2025-01-17',
    allocated_capacity: '800',
    priority: 1,
    status: 'PLANNED' as const,
    created_at: '2025-01-01T00:00:00Z',
  }

  describe('Form Rendering', () => {
    it('should render create form with pre-selected lane and date', () => {
      render(
        <AssignmentForm
          preSelectedLane={5}
          preSelectedDate="2025-01-20"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      expect(screen.getByLabelText(/lane id/i)).toHaveValue(5)
      expect(screen.getByLabelText(/start date/i)).toHaveValue('2025-01-20')
      expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
    })

    it('should render edit form with existing assignment data', () => {
      render(
        <AssignmentForm
          assignment={mockAssignment}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      expect(screen.getByLabelText(/lane id/i)).toHaveValue(5)
      expect(screen.getByLabelText(/work order id/i)).toHaveValue(500)
      expect(screen.getByLabelText(/start date/i)).toHaveValue('2025-01-15')
      expect(screen.getByLabelText(/end date/i)).toHaveValue('2025-01-17')
      // Number inputs store value as string in the DOM
      expect((screen.getByLabelText(/allocated capacity/i) as HTMLInputElement).value).toBe('800')
      expect(screen.getByLabelText(/priority/i)).toHaveValue(1)
      expect(screen.getByRole('button', { name: /update/i })).toBeInTheDocument()
    })

    it('should show status dropdown only in edit mode', () => {
      const { rerender } = render(
        <AssignmentForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      expect(screen.queryByLabelText(/status/i)).not.toBeInTheDocument()

      rerender(
        <AssignmentForm
          assignment={mockAssignment}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      expect(screen.getByLabelText(/status/i)).toBeInTheDocument()
    })

    it('should disable lane and work order fields in edit mode', () => {
      render(
        <AssignmentForm
          assignment={mockAssignment}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      expect(screen.getByLabelText(/lane id/i)).toBeDisabled()
      expect(screen.getByLabelText(/work order id/i)).toBeDisabled()
    })
  })

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      const user = userEvent.setup()

      render(
        <AssignmentForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      const submitButton = screen.getByRole('button', { name: /create/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/lane is required/i)).toBeInTheDocument()
        expect(screen.getByText(/work order is required/i)).toBeInTheDocument()
        expect(screen.getByText(/start date is required/i)).toBeInTheDocument()
        expect(screen.getByText(/end date is required/i)).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('should validate allocated capacity is greater than 0', async () => {
      const user = userEvent.setup()

      render(
        <AssignmentForm
          preSelectedLane={5}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      const laneInput = screen.getByLabelText(/lane id/i)
      const woInput = screen.getByLabelText(/work order id/i)
      const startInput = screen.getByLabelText(/start date/i)
      const endInput = screen.getByLabelText(/end date/i)
      const capacityInput = screen.getByLabelText(/allocated capacity/i)

      await user.clear(laneInput)
      await user.type(laneInput, '5')
      await user.clear(woInput)
      await user.type(woInput, '500')
      await user.type(startInput, '2025-01-15')
      await user.type(endInput, '2025-01-17')
      await user.clear(capacityInput)
      await user.type(capacityInput, '0')

      const submitButton = screen.getByRole('button', { name: /create/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/capacity must be greater than 0/i)).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('should validate end date is on or after start date', async () => {
      const user = userEvent.setup()

      render(
        <AssignmentForm
          preSelectedLane={5}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      const laneInput = screen.getByLabelText(/lane id/i)
      const woInput = screen.getByLabelText(/work order id/i)
      const startInput = screen.getByLabelText(/start date/i)
      const endInput = screen.getByLabelText(/end date/i)
      const capacityInput = screen.getByLabelText(/allocated capacity/i)

      await user.clear(laneInput)
      await user.type(laneInput, '5')
      await user.clear(woInput)
      await user.type(woInput, '500')
      await user.type(startInput, '2025-01-20')
      await user.type(endInput, '2025-01-15')
      await user.clear(capacityInput)
      await user.type(capacityInput, '800')

      const submitButton = screen.getByRole('button', { name: /create/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/end date must be on or after start date/i)).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })
  })

  describe('Form Submission', () => {
    it('should submit valid create form with auth store values', async () => {
      const user = userEvent.setup()
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <AssignmentForm
          preSelectedLane={5}
          preSelectedDate="2025-01-15"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      const woInput = screen.getByLabelText(/work order id/i)
      const endInput = screen.getByLabelText(/end date/i)
      const capacityInput = screen.getByLabelText(/allocated capacity/i)
      const priorityInput = screen.getByLabelText(/priority/i)

      await user.clear(woInput)
      await user.type(woInput, '500')
      // Use fireEvent for date inputs
      fireEvent.change(endInput, { target: { value: '2025-01-17' } })
      await user.clear(capacityInput)
      await user.type(capacityInput, '800')
      await user.clear(priorityInput)
      await user.type(priorityInput, '1')

      const submitButton = screen.getByRole('button', { name: /create/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            organization_id: 1,
            plant_id: 100,
            lane_id: 5,
            work_order_id: 500,
            scheduled_start: '2025-01-15',
            scheduled_end: '2025-01-17',
            allocated_capacity: '800',
            priority: 1,
          })
        )
      })
    })

    it('should submit valid update form', async () => {
      const user = userEvent.setup()
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <AssignmentForm
          assignment={mockAssignment}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      const capacityInput = screen.getByLabelText(/allocated capacity/i)
      await user.clear(capacityInput)
      await user.type(capacityInput, '1000')

      const submitButton = screen.getByRole('button', { name: /update/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            allocated_capacity: '1000',
            scheduled_start: '2025-01-15',
            scheduled_end: '2025-01-17',
            priority: 1,
            status: 'PLANNED',
          })
        )
      })
    })
  })

  describe('Form Interactions', () => {
    it('should call onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <AssignmentForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(mockOnCancel).toHaveBeenCalled()
      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('should disable all fields and buttons when loading', () => {
      render(
        <AssignmentForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={true}
        />
      )

      expect(screen.getByLabelText(/lane id/i)).toBeDisabled()
      expect(screen.getByLabelText(/work order id/i)).toBeDisabled()
      expect(screen.getByLabelText(/start date/i)).toBeDisabled()
      expect(screen.getByLabelText(/end date/i)).toBeDisabled()
      expect(screen.getByLabelText(/allocated capacity/i)).toBeDisabled()
      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled()
      expect(screen.getByText(/saving\.\.\./i)).toBeInTheDocument()
    })

    it('should update status in edit mode', async () => {
      const user = userEvent.setup()
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <AssignmentForm
          assignment={mockAssignment}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      const statusSelect = screen.getByLabelText(/status/i)
      await user.selectOptions(statusSelect, 'ACTIVE')

      const submitButton = screen.getByRole('button', { name: /update/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            status: 'ACTIVE',
          })
        )
      })
    })
  })
})
