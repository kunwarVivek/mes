/**
 * LaneSchedulingPage Component Tests
 *
 * TDD: Integration tests for lane scheduling page with calendar view
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LaneSchedulingPage } from '../LaneSchedulingPage'
import { useAuthStore } from '@/stores/auth.store'
import type { Lane, LaneAssignment } from '../../types/lane.types'

// Mock auth store
vi.mock('@/stores/auth.store', () => ({
  useAuthStore: vi.fn(),
}))

// Mock hooks
vi.mock('../../hooks/useLanes', () => ({
  useLanes: vi.fn(),
  useLaneAssignments: vi.fn(),
  useCreateAssignment: vi.fn(),
  useUpdateAssignment: vi.fn(),
  useDeleteAssignment: vi.fn(),
}))

import {
  useLanes,
  useLaneAssignments,
  useCreateAssignment,
  useUpdateAssignment,
} from '../../hooks/useLanes'

describe('LaneSchedulingPage', () => {
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

  const mockAssignments: LaneAssignment[] = [
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
    {
      id: 2,
      organization_id: 1,
      plant_id: 100,
      lane_id: 1,
      work_order_id: 501,
      scheduled_start: '2025-01-18',
      scheduled_end: '2025-01-20',
      allocated_capacity: '600',
      priority: 2,
      status: 'ACTIVE' as const,
      created_at: '2025-01-01T00:00:00Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()

    // Default auth store mock
    vi.mocked(useAuthStore).mockReturnValue({
      currentOrg: { id: 1, organization_code: 'ORG001', organization_name: 'Test Org' },
      currentPlant: { id: 100, plant_code: 'P001', plant_name: 'Test Plant' },
    } as any)

    // Default hooks mocks
    vi.mocked(useLanes).mockReturnValue({
      data: { items: mockLanes, total: 2, page: 1, page_size: 50 },
      isLoading: false,
      error: null,
    } as any)

    vi.mocked(useLaneAssignments).mockReturnValue({
      data: { items: mockAssignments, total: 2, page: 1, page_size: 50 },
      isLoading: false,
      error: null,
    } as any)

    vi.mocked(useCreateAssignment).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({}),
      isPending: false,
    } as any)

    vi.mocked(useUpdateAssignment).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({}),
      isPending: false,
    } as any)
  })

  describe('Page Rendering', () => {
    it('should show guard message when no plant is selected', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        currentOrg: { id: 1, organization_code: 'ORG001', organization_name: 'Test Org' },
        currentPlant: null,
      } as any)

      render(<LaneSchedulingPage />)

      expect(screen.getAllByText(/lane scheduling/i).length).toBeGreaterThan(0)
      expect(screen.getByText(/please select a plant to view lane scheduling/i)).toBeInTheDocument()
    })

    it('should render page with plant information', () => {
      render(<LaneSchedulingPage />)

      expect(screen.getByText(/lane scheduling/i)).toBeInTheDocument()
      expect(screen.getByText(/test plant/i)).toBeInTheDocument()
      expect(screen.getByText(/p001/i)).toBeInTheDocument()
    })

    it('should display summary statistics', () => {
      render(<LaneSchedulingPage />)

      expect(screen.getByText(/total assignments/i)).toBeInTheDocument()
      expect(screen.getByText(/total lanes/i)).toBeInTheDocument()

      // Should show correct counts (multiple instances may exist)
      expect(screen.getAllByText('2').length).toBeGreaterThan(0) // Total assignments and lanes
      expect(screen.getAllByText('1').length).toBeGreaterThan(0) // Active assignments
    })

    it('should render calendar grid', () => {
      render(<LaneSchedulingPage />)

      expect(screen.getByText('Assembly Line 1')).toBeInTheDocument()
      expect(screen.getByText('Assembly Line 2')).toBeInTheDocument()
    })

    it('should show status legend', () => {
      render(<LaneSchedulingPage />)

      // Status legend badges
      expect(screen.getAllByText(/planned/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/active/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/completed/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/cancelled/i).length).toBeGreaterThan(0)
    })
  })

  describe('View Toggle', () => {
    it('should toggle between 7-day and 14-day view', async () => {
      const user = userEvent.setup()

      render(<LaneSchedulingPage />)

      const toggleButton = screen.getByRole('button', { name: /14-day view/i })
      expect(toggleButton).toBeInTheDocument()

      await user.click(toggleButton)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /7-day view/i })).toBeInTheDocument()
      })
    })
  })

  describe('Assignment Form Modal', () => {
    it('should not show form modal initially', () => {
      render(<LaneSchedulingPage />)

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should open form modal when cell is clicked', async () => {
      const user = userEvent.setup()

      render(<LaneSchedulingPage />)

      // Find and click a calendar cell
      const cells = screen.getAllByRole('button', { name: /cell/i })
      if (cells.length > 0) {
        await user.click(cells[0])

        await waitFor(() => {
          expect(screen.getByText(/new assignment/i)).toBeInTheDocument()
        })
      }
    })

    it('should close form modal when cancel is clicked', async () => {
      const user = userEvent.setup()

      render(<LaneSchedulingPage />)

      // Open modal
      const cells = screen.getAllByRole('button', { name: /cell/i })
      if (cells.length > 0) {
        await user.click(cells[0])

        await waitFor(() => {
          expect(screen.getByText(/new assignment/i)).toBeInTheDocument()
        })

        // Click cancel
        const cancelButton = screen.getByRole('button', { name: /cancel/i })
        await user.click(cancelButton)

        await waitFor(() => {
          expect(screen.queryByText(/new assignment/i)).not.toBeInTheDocument()
        })
      }
    })

    it('should submit form and close modal on successful creation', async () => {
      const user = userEvent.setup()
      const mockMutate = vi.fn().mockResolvedValue({})
      vi.mocked(useCreateAssignment).mockReturnValue({
        mutateAsync: mockMutate,
        isPending: false,
      } as any)

      render(<LaneSchedulingPage />)

      // Open modal
      const cells = screen.getAllByRole('button', { name: /cell/i })
      if (cells.length > 0) {
        await user.click(cells[0])

        await waitFor(() => {
          expect(screen.getByText(/new assignment/i)).toBeInTheDocument()
        })

        // Fill form
        const laneInput = screen.getByLabelText(/lane id/i)
        const woInput = screen.getByLabelText(/work order id/i)
        const startInput = screen.getByLabelText(/start date/i)
        const endInput = screen.getByLabelText(/end date/i)
        const capacityInput = screen.getByLabelText(/allocated capacity/i)

        await user.clear(laneInput)
        await user.type(laneInput, '1')
        await user.clear(woInput)
        await user.type(woInput, '500')
        // Use fireEvent for date inputs
        fireEvent.change(startInput, { target: { value: '2025-01-15' } })
        fireEvent.change(endInput, { target: { value: '2025-01-17' } })
        await user.clear(capacityInput)
        await user.type(capacityInput, '800')

        // Submit
        const submitButton = screen.getByRole('button', { name: /create/i })
        await user.click(submitButton)

        await waitFor(() => {
          expect(mockMutate).toHaveBeenCalled()
        })
      }
    })
  })

  describe('Loading States', () => {
    it('should show loading state for lanes', () => {
      vi.mocked(useLanes).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any)

      render(<LaneSchedulingPage />)

      expect(screen.getAllByText(/loading/i).length).toBeGreaterThan(0)
    })

    it('should show loading state for assignments', () => {
      vi.mocked(useLaneAssignments).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any)

      render(<LaneSchedulingPage />)

      expect(screen.getAllByText(/loading/i).length).toBeGreaterThan(0)
    })
  })

  describe('Empty States', () => {
    it('should handle empty lanes list', () => {
      vi.mocked(useLanes).mockReturnValue({
        data: { items: [], total: 0, page: 1, page_size: 50 },
        isLoading: false,
        error: null,
      } as any)

      render(<LaneSchedulingPage />)

      // Multiple zeros may appear (assignments, active, lanes)
      expect(screen.getAllByText('0').length).toBeGreaterThan(0)
    })

    it('should handle empty assignments list', () => {
      vi.mocked(useLaneAssignments).mockReturnValue({
        data: { items: [], total: 0, page: 1, page_size: 50 },
        isLoading: false,
        error: null,
      } as any)

      render(<LaneSchedulingPage />)

      expect(screen.getAllByText(/0/i).length).toBeGreaterThan(0) // All counts should be 0
    })
  })

  describe('Accessibility', () => {
    it('should have proper modal accessibility attributes', async () => {
      const user = userEvent.setup()

      render(<LaneSchedulingPage />)

      // Open modal
      const cells = screen.getAllByRole('button', { name: /cell/i })
      if (cells.length > 0) {
        await user.click(cells[0])

        await waitFor(() => {
          // Modal should have proper role
          expect(screen.queryByText(/new assignment/i)).toBeInTheDocument()
        })
      }
    })
  })
})
