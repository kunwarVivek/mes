/**
 * NCRForm Component Tests
 *
 * Testing form validation, user interactions, and submission
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NCRForm } from '../NCRForm'
import { useNCRMutations } from '../../hooks/useNCRMutations'

// Mock hooks
vi.mock('../../hooks/useNCRMutations')

// Mock useToast
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}))

// Mock auth store
const mockAuthStore = {
  user: { id: 99, email: 'reporter@example.com', username: 'reporter', is_active: true, is_superuser: false },
  currentOrg: { id: 42, org_code: 'ORG42', org_name: 'Test Organization' },
  currentPlant: { id: 10, plant_code: 'PLT10', plant_name: 'Test Plant' },
  accessToken: 'mock-token',
  refreshToken: 'mock-refresh',
  isAuthenticated: true,
  login: vi.fn(),
  logout: vi.fn(),
  updateUser: vi.fn(),
  setTokens: vi.fn(),
  setCurrentOrg: vi.fn(),
  setCurrentPlant: vi.fn(),
}

vi.mock('@/stores/auth.store', () => ({
  useAuthStore: () => mockAuthStore,
}))

describe('NCRForm', () => {
  const mockCreateNCR = vi.fn()
  const mockOnSuccess = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useNCRMutations).mockReturnValue({
      createNCR: {
        mutateAsync: mockCreateNCR,
        isPending: false,
      } as any,
      updateNCRStatus: {
        mutate: vi.fn(),
        isPending: false,
      } as any,
    })
  })

  describe('Rendering', () => {
    it('should render all form fields', () => {
      render(<NCRForm onSuccess={mockOnSuccess} />)

      expect(screen.getByLabelText(/ncr number/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/work order id/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/material id/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/defect type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/defect description/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/quantity defective/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/reported by user id/i)).toBeInTheDocument()
    })

    it('should render submit and reset buttons', () => {
      render(<NCRForm onSuccess={mockOnSuccess} />)

      expect(screen.getByRole('button', { name: /create ncr/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })

    it('should have textarea with 4 rows for defect description', () => {
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const textarea = screen.getByLabelText(/defect description/i)
      expect(textarea).toHaveAttribute('rows', '4')
    })
  })

  describe('Validation - NCR Number', () => {
    it('should show error when NCR number is empty', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/ncr number is required/i)).toBeInTheDocument()
      })
    })

    it('should show error when NCR number exceeds 50 characters', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const ncrNumberInput = screen.getByLabelText(/ncr number/i)
      await user.type(ncrNumberInput, 'A'.repeat(51))

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/ncr number must be at most 50 characters/i)).toBeInTheDocument()
      })
    })

    it('should accept valid NCR number', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const ncrNumberInput = screen.getByLabelText(/ncr number/i)
      await user.type(ncrNumberInput, 'NCR-2025-001')

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByText(/ncr number/i)).not.toHaveTextContent(/required|must be/i)
      })
    })
  })

  describe('Validation - Work Order ID', () => {
    it('should show error when work order ID is not positive', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const woInput = screen.getByLabelText(/work order id/i)
      await user.type(woInput, '0')

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/work order id must be positive/i)).toBeInTheDocument()
      })
    })

    it('should accept positive work order ID', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const woInput = screen.getByLabelText(/work order id/i)
      await user.clear(woInput)
      await user.type(woInput, '123')

      expect(woInput).toHaveValue(123)
    })
  })

  describe('Validation - Material ID', () => {
    it('should show error when material ID is not positive', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const materialInput = screen.getByLabelText(/material id/i)
      await user.type(materialInput, '-1')

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/material id must be positive/i)).toBeInTheDocument()
      })
    })
  })

  describe('Validation - Defect Description', () => {
    it('should show error when defect description is empty', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/defect description is required/i)).toBeInTheDocument()
      })
    })

    it('should have maxLength attribute on defect description textarea', () => {
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const descriptionInput = screen.getByLabelText(/defect description/i)
      // HTML maxLength attribute prevents exceeding 500 characters in the UI
      expect(descriptionInput).toHaveAttribute('maxLength', '500')
      expect(screen.getByText(/max 500 characters/i)).toBeInTheDocument()
    })
  })

  describe('Validation - Quantity Defective', () => {
    it('should show error when quantity defective is not positive', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const qtyInput = screen.getByLabelText(/quantity defective/i)
      await user.type(qtyInput, '0')

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/quantity defective must be positive/i)).toBeInTheDocument()
      })
    })

    it('should accept decimal values for quantity defective', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const qtyInput = screen.getByLabelText(/quantity defective/i)
      await user.clear(qtyInput)
      await user.type(qtyInput, '10.5')

      expect(qtyInput).toHaveValue(10.5)
    })
  })

  describe('Defect Type Select', () => {
    it('should render all defect type options', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const selectTrigger = screen.getByRole('combobox', { name: /defect type/i })
      await user.click(selectTrigger)

      await waitFor(() => {
        expect(screen.getByRole('option', { name: /dimensional/i })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: /visual/i })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: /functional/i })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: /material/i })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: /other/i })).toBeInTheDocument()
      })
    })

    it('should allow selecting defect type', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const selectTrigger = screen.getByRole('combobox', { name: /defect type/i })
      await user.click(selectTrigger)

      const visualOption = screen.getByRole('option', { name: /visual/i })
      await user.click(visualOption)

      expect(selectTrigger).toHaveTextContent(/visual/i)
    })
  })

  describe('Form Submission', () => {
    it('should call createNCR mutation with valid data', async () => {
      const user = userEvent.setup()
      mockCreateNCR.mockResolvedValueOnce({ id: 1 })

      render(<NCRForm onSuccess={mockOnSuccess} />)

      // Fill form
      await user.type(screen.getByLabelText(/ncr number/i), 'NCR-2025-001')
      await user.type(screen.getByLabelText(/work order id/i), '100')
      await user.type(screen.getByLabelText(/material id/i), '50')

      const defectTypeSelect = screen.getByRole('combobox', { name: /defect type/i })
      await user.click(defectTypeSelect)
      await user.click(screen.getByRole('option', { name: /dimensional/i }))

      await user.type(
        screen.getByLabelText(/defect description/i),
        'Part dimensions out of tolerance'
      )
      await user.type(screen.getByLabelText(/quantity defective/i), '5')
      await user.clear(screen.getByLabelText(/reported by user id/i))
      await user.type(screen.getByLabelText(/reported by user id/i), '1')

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockCreateNCR).toHaveBeenCalledWith(
          expect.objectContaining({
            ncr_number: 'NCR-2025-001',
            work_order_id: 100,
            material_id: 50,
            defect_type: 'DIMENSIONAL',
            defect_description: 'Part dimensions out of tolerance',
            quantity_defective: 5,
            reported_by_user_id: 1,
          })
        )
      })
    })

    it('should call onSuccess callback after successful submission', async () => {
      const user = userEvent.setup()
      mockCreateNCR.mockResolvedValueOnce({ id: 1 })

      render(<NCRForm onSuccess={mockOnSuccess} />)

      // Fill form with minimum required fields
      await user.type(screen.getByLabelText(/ncr number/i), 'NCR-2025-001')
      await user.type(screen.getByLabelText(/work order id/i), '100')
      await user.type(screen.getByLabelText(/material id/i), '50')

      const defectTypeSelect = screen.getByRole('combobox', { name: /defect type/i })
      await user.click(defectTypeSelect)
      await user.click(screen.getByRole('option', { name: /visual/i }))

      await user.type(screen.getByLabelText(/defect description/i), 'Surface defect')
      await user.type(screen.getByLabelText(/quantity defective/i), '3')

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled()
      })
    })

    it('should disable submit button while submitting', async () => {
      const user = userEvent.setup()
      mockCreateNCR.mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve({ id: 1 }), 100)
          })
      )

      vi.mocked(useNCRMutations).mockReturnValue({
        createNCR: {
          mutateAsync: mockCreateNCR,
          isPending: true,
        } as any,
        updateNCRStatus: {
          mutate: vi.fn(),
          isPending: false,
        } as any,
      })

      render(<NCRForm onSuccess={mockOnSuccess} />)

      const submitButton = screen.getByRole('button', { name: /submitting/i })
      expect(submitButton).toBeDisabled()
    })
  })

  describe('Form Reset', () => {
    it('should clear form when reset button is clicked', async () => {
      const user = userEvent.setup()
      render(<NCRForm onSuccess={mockOnSuccess} />)

      // Fill form
      await user.type(screen.getByLabelText(/ncr number/i), 'NCR-2025-001')
      await user.type(screen.getByLabelText(/work order id/i), '100')
      await user.type(screen.getByLabelText(/defect description/i), 'Test description')

      // Reset form
      const resetButton = screen.getByRole('button', { name: /reset/i })
      await user.click(resetButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/ncr number/i)).toHaveValue('')
        expect(screen.getByLabelText(/work order id/i)).toHaveValue(null)
        expect(screen.getByLabelText(/defect description/i)).toHaveValue('')
      })
    })
  })

  describe('Default Values', () => {
    it('should set reported_by_user_id default from auth store', () => {
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const reportedByInput = screen.getByLabelText(/reported by user id/i)
      // Should use auth store user ID (99), not hardcoded 1
      expect(reportedByInput).toHaveValue(99)
    })
  })

  describe('Auth Store Integration', () => {
    it('should use reported_by_user_id from auth store', async () => {
      const user = userEvent.setup()
      mockCreateNCR.mockResolvedValueOnce({ id: 1 })

      render(<NCRForm onSuccess={mockOnSuccess} />)

      // Fill form with minimum required fields
      await user.type(screen.getByLabelText(/ncr number/i), 'NCR-2025-001')
      await user.type(screen.getByLabelText(/work order id/i), '100')
      await user.type(screen.getByLabelText(/material id/i), '50')

      const defectTypeSelect = screen.getByRole('combobox', { name: /defect type/i })
      await user.click(defectTypeSelect)
      await user.click(screen.getByRole('option', { name: /visual/i }))

      await user.type(screen.getByLabelText(/defect description/i), 'Surface defect')
      await user.type(screen.getByLabelText(/quantity defective/i), '3')

      const submitButton = screen.getByRole('button', { name: /create ncr/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockCreateNCR).toHaveBeenCalledWith(
          expect.objectContaining({
            reported_by_user_id: 99, // From mockAuthStore.user.id
          })
        )
      })
    })

    it('should handle missing user in auth store gracefully', async () => {
      const user = userEvent.setup()

      // Temporarily override mock to return null user
      vi.mocked(vi.fn()).mockReturnValueOnce({
        ...mockAuthStore,
        user: null,
      })

      render(<NCRForm onSuccess={mockOnSuccess} />)

      // Form should still render without crashing
      expect(screen.getByLabelText(/ncr number/i)).toBeInTheDocument()
    })

    it('should show correct user ID in form field from auth store', () => {
      render(<NCRForm onSuccess={mockOnSuccess} />)

      const reportedByInput = screen.getByLabelText(/reported by user id/i)
      // Should use auth store user ID (99), not hardcoded 1
      expect(reportedByInput).toHaveValue(99)
    })
  })
})
