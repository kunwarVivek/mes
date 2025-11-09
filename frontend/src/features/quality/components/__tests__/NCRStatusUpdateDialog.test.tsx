/**
 * NCRStatusUpdateDialog Component Tests
 *
 * Testing status update dialog with conditional resolution notes
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NCRStatusUpdateDialog } from '../NCRStatusUpdateDialog'
import { useNCRMutations } from '../../hooks/useNCRMutations'
import type { NCR } from '../../schemas/ncr.schema'

// Mock hooks
vi.mock('../../hooks/useNCRMutations')

// Mock useToast
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}))

describe('NCRStatusUpdateDialog', () => {
  const mockUpdateStatus = vi.fn()
  const mockOnOpenChange = vi.fn()

  const mockNCR: NCR = {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2025-001',
    work_order_id: 100,
    material_id: 50,
    defect_type: 'DIMENSIONAL',
    defect_description: 'Test defect',
    quantity_defective: 5,
    status: 'OPEN',
    reported_by_user_id: 1,
    created_at: new Date('2025-01-01'),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useNCRMutations).mockReturnValue({
      createNCR: {
        mutateAsync: vi.fn(),
        isPending: false,
      } as any,
      updateNCRStatus: {
        mutate: mockUpdateStatus,
        isPending: false,
      } as any,
    })
  })

  describe('Rendering', () => {
    it('should not render when open is false', () => {
      render(
        <NCRStatusUpdateDialog ncr={mockNCR} open={false} onOpenChange={mockOnOpenChange} />
      )

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should render dialog when open is true', () => {
      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText(/update ncr status/i)).toBeInTheDocument()
    })

    it('should display NCR number in dialog', () => {
      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      expect(screen.getByText(/NCR-2025-001/i)).toBeInTheDocument()
    })
  })

  describe('Status Selection', () => {
    it('should show valid status transitions from OPEN', async () => {
      const user = userEvent.setup()
      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)

      expect(screen.getByRole('option', { name: /in review/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /resolved/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /closed/i })).toBeInTheDocument()
    })

    it('should show valid status transitions from IN_REVIEW', async () => {
      const user = userEvent.setup()
      const inReviewNCR = { ...mockNCR, status: 'IN_REVIEW' as const }

      render(
        <NCRStatusUpdateDialog ncr={inReviewNCR} open={true} onOpenChange={mockOnOpenChange} />
      )

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)

      expect(screen.getByRole('option', { name: /resolved/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /closed/i })).toBeInTheDocument()
    })

    it('should show valid status transitions from RESOLVED', async () => {
      const user = userEvent.setup()
      const resolvedNCR = { ...mockNCR, status: 'RESOLVED' as const }

      render(
        <NCRStatusUpdateDialog ncr={resolvedNCR} open={true} onOpenChange={mockOnOpenChange} />
      )

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)

      expect(screen.getByRole('option', { name: /closed/i })).toBeInTheDocument()
    })
  })

  describe('Resolution Notes Conditional Rendering', () => {
    it('should not show resolution notes field initially', () => {
      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      expect(screen.queryByLabelText(/resolution notes/i)).not.toBeInTheDocument()
    })

    it('should show resolution notes field when RESOLVED is selected', async () => {
      const user = userEvent.setup()
      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)
      await user.click(screen.getByRole('option', { name: /resolved/i }))

      await waitFor(() => {
        expect(screen.getByLabelText(/resolution notes/i)).toBeInTheDocument()
      })
    })

    it('should not show resolution notes for other statuses', async () => {
      const user = userEvent.setup()
      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)
      await user.click(screen.getByRole('option', { name: /in review/i }))

      await waitFor(() => {
        expect(screen.queryByLabelText(/resolution notes/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Form Validation', () => {
    it('should show error when resolution notes are missing for RESOLVED status', async () => {
      const user = userEvent.setup()
      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)
      await user.click(screen.getByRole('option', { name: /resolved/i }))

      const updateButton = screen.getByRole('button', { name: /update status/i })
      await user.click(updateButton)

      await waitFor(() => {
        expect(
          screen.getByText(/resolution notes are required when status is resolved/i)
        ).toBeInTheDocument()
      })
    })

    it('should not show error for IN_REVIEW without resolution notes', async () => {
      const user = userEvent.setup()
      mockUpdateStatus.mockResolvedValueOnce({ id: 1 })

      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)
      await user.click(screen.getByRole('option', { name: /in review/i }))

      const updateButton = screen.getByRole('button', { name: /update status/i })
      await user.click(updateButton)

      await waitFor(() => {
        expect(mockUpdateStatus).toHaveBeenCalled()
      })
    })
  })

  describe('Form Submission', () => {
    it('should call updateNCRStatus with correct data', async () => {
      const user = userEvent.setup()
      mockUpdateStatus.mockImplementation((args, options) => {
        options?.onSuccess?.()
      })

      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)
      await user.click(screen.getByRole('option', { name: /in review/i }))

      const updateButton = screen.getByRole('button', { name: /update status/i })
      await user.click(updateButton)

      await waitFor(() => {
        expect(mockUpdateStatus).toHaveBeenCalledWith(
          {
            id: 1,
            data: expect.objectContaining({
              status: 'IN_REVIEW',
            }),
          },
          expect.any(Object)
        )
      })
    })

    it('should include resolution notes when RESOLVED', async () => {
      const user = userEvent.setup()
      mockUpdateStatus.mockImplementation((args, options) => {
        options?.onSuccess?.()
      })

      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)
      await user.click(screen.getByRole('option', { name: /resolved/i }))

      const resolutionNotesInput = screen.getByLabelText(/resolution notes/i)
      await user.type(resolutionNotesInput, 'Issue resolved by rework')

      const updateButton = screen.getByRole('button', { name: /update status/i })
      await user.click(updateButton)

      await waitFor(() => {
        expect(mockUpdateStatus).toHaveBeenCalledWith(
          {
            id: 1,
            data: expect.objectContaining({
              status: 'RESOLVED',
              resolution_notes: 'Issue resolved by rework',
            }),
          },
          expect.any(Object)
        )
      })
    })

    it('should close dialog on successful submission', async () => {
      const user = userEvent.setup()
      mockUpdateStatus.mockImplementation((args, options) => {
        options?.onSuccess?.()
      })

      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const statusSelect = screen.getByRole('combobox', { name: /status/i })
      await user.click(statusSelect)
      await user.click(screen.getByRole('option', { name: /in review/i }))

      const updateButton = screen.getByRole('button', { name: /update status/i })
      await user.click(updateButton)

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false)
      })
    })
  })

  describe('Cancel Action', () => {
    it('should close dialog when cancel button is clicked', async () => {
      const user = userEvent.setup()
      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(mockOnOpenChange).toHaveBeenCalledWith(false)
    })
  })

  describe('Loading State', () => {
    it('should disable buttons while submitting', () => {
      vi.mocked(useNCRMutations).mockReturnValue({
        createNCR: {
          mutateAsync: vi.fn(),
          isPending: false,
        } as any,
        updateNCRStatus: {
          mutate: mockUpdateStatus,
          isPending: true,
        } as any,
      })

      render(<NCRStatusUpdateDialog ncr={mockNCR} open={true} onOpenChange={mockOnOpenChange} />)

      const updateButton = screen.getByRole('button', { name: /updating/i })
      expect(updateButton).toBeDisabled()
    })
  })
})
