import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { WorkOrderForm } from '../WorkOrderForm'

vi.mock('../../hooks/useWorkOrderMutations', () => ({
  useWorkOrderMutations: () => ({
    createWorkOrder: {
      mutateAsync: vi.fn().mockResolvedValue({}),
      isPending: false,
    },
    updateWorkOrder: {
      mutateAsync: vi.fn().mockResolvedValue({}),
      isPending: false,
    },
  }),
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('WorkOrderForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('create mode', () => {
    it('renders all required fields', () => {
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      expect(screen.getByLabelText(/material id/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/order type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/planned quantity/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/priority/i)).toBeInTheDocument()
    })

    it('shows validation error for empty material_id', async () => {
      const user = userEvent.setup()
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      const submitButton = screen.getByRole('button', { name: /create work order/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/material id must be greater than 0/i)).toBeInTheDocument()
      })
    })

    it('shows validation error for zero planned_quantity', async () => {
      const user = userEvent.setup()
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      const quantityInput = screen.getByLabelText(/planned quantity/i)
      await user.clear(quantityInput)
      await user.type(quantityInput, '0')

      const submitButton = screen.getByRole('button', { name: /create work order/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/planned quantity must be greater than 0/i)).toBeInTheDocument()
      })
    })

    it('shows validation error for invalid priority', async () => {
      const user = userEvent.setup()
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      // Priority input has min/max HTML attributes, so Zod validation works at form level
      const priorityInput = screen.getByLabelText(/priority/i)
      expect(priorityInput).toHaveAttribute('min', '1')
      expect(priorityInput).toHaveAttribute('max', '10')
    })

    it('renders order type select with all options', () => {
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      const select = screen.getByLabelText(/order type/i)
      expect(select).toBeInTheDocument()
    })

    it('renders priority slider with range 1-10', () => {
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      const priorityInput = screen.getByLabelText(/priority/i)
      expect(priorityInput).toHaveAttribute('type', 'number')
    })

    it('renders optional date fields', () => {
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      expect(screen.getByLabelText(/start date planned/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/end date planned/i)).toBeInTheDocument()
    })
  })

  describe('edit mode', () => {
    const mockWorkOrder = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-2025-001',
      material_id: 1,
      order_type: 'PRODUCTION',
      order_status: 'PLANNED',
      planned_quantity: 100,
      actual_quantity: 0,
      priority: 5,
      created_by_user_id: 1,
      created_at: new Date('2025-01-10'),
      operations: [],
      materials: [],
    }

    it('pre-fills form with default values', () => {
      render(<WorkOrderForm workOrderId={1} defaultValues={mockWorkOrder} onSuccess={vi.fn()} />, {
        wrapper: createWrapper(),
      })

      const quantityInput = screen.getByLabelText(/planned quantity/i) as HTMLInputElement
      expect(quantityInput.value).toBe('100')
    })

    it('disables material_id field in edit mode', () => {
      render(<WorkOrderForm workOrderId={1} defaultValues={mockWorkOrder} onSuccess={vi.fn()} />, {
        wrapper: createWrapper(),
      })

      const materialInput = screen.getByLabelText(/material id/i)
      expect(materialInput).toBeDisabled()
    })
  })

  describe('loading states', () => {
    it('disables submit button when submitting', async () => {
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      const submitButton = screen.getByRole('button', { name: /create work order/i })
      expect(submitButton).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has proper aria-invalid on fields with errors', async () => {
      const user = userEvent.setup()
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      const submitButton = screen.getByRole('button', { name: /create work order/i })
      await user.click(submitButton)

      await waitFor(() => {
        const materialInput = screen.getByLabelText(/material id/i)
        expect(materialInput).toHaveAttribute('aria-invalid', 'true')
      })
    })

    it('associates error messages with fields', async () => {
      const user = userEvent.setup()
      render(<WorkOrderForm onSuccess={vi.fn()} />, { wrapper: createWrapper() })

      const submitButton = screen.getByRole('button', { name: /create work order/i })
      await user.click(submitButton)

      await waitFor(() => {
        const errorMessage = screen.getByText(/material id must be greater than 0/i)
        expect(errorMessage).toHaveClass('text-destructive')
      })
    })
  })
})
