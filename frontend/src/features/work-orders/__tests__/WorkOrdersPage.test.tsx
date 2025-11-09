/**
 * WorkOrdersPage Component Tests
 *
 * TDD: RED → GREEN → REFACTOR
 * Testing the complete Work Orders Page with CRUD functionality
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { WorkOrdersPage } from '../pages/WorkOrdersPage'
import { workOrderService } from '../services/workOrder.service'
import type { ReactNode } from 'react'

vi.mock('../services/workOrder.service')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('WorkOrdersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render page title', () => {
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Work Orders')).toBeInTheDocument()
  })

  it('should render create button', () => {
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
  })

  it('should display work orders in table', async () => {
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_number: 'WO001',
          material_id: 1,
          order_type: 'PRODUCTION',
          order_status: 'PLANNED',
          planned_quantity: 100,
          actual_quantity: 0,
          start_date_planned: '2025-11-10',
          end_date_planned: '2025-11-15',
          priority: 5,
          created_by_user_id: 1,
          created_at: '2025-11-09T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('WO001')).toBeInTheDocument()
    })

    expect(screen.getByText('PRODUCTION')).toBeInTheDocument()
    expect(screen.getByText('PLANNED')).toBeInTheDocument()
  })

  it('should show form when create button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    await user.click(screen.getByRole('button', { name: /create/i }))

    expect(screen.getByLabelText(/material id/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/planned quantity/i)).toBeInTheDocument()
  })

  it('should create work order when form is submitted', async () => {
    const user = userEvent.setup()
    const mockCreatedWorkOrder = {
      id: 2,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO002',
      material_id: 123,
      order_type: 'PRODUCTION' as const,
      order_status: 'PLANNED' as const,
      planned_quantity: 200,
      actual_quantity: 0,
      priority: 5,
      created_by_user_id: 1,
      created_at: '2025-11-09T00:00:00Z',
    }

    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })

    vi.mocked(workOrderService.create).mockResolvedValue(mockCreatedWorkOrder)

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    // Open form
    await user.click(screen.getByRole('button', { name: /create/i }))

    // Fill form
    await user.type(screen.getByLabelText(/material id/i), '123')
    await user.type(screen.getByLabelText(/planned quantity/i), '200')

    // Submit - get the submit button specifically (the one in the form)
    const submitButtons = screen.getAllByRole('button', { name: /create work order/i })
    const submitButton = submitButtons[1] // The form submit button is the second one
    await user.click(submitButton)

    await waitFor(() => {
      expect(workOrderService.create).toHaveBeenCalledWith(
        expect.objectContaining({
          material_id: 123,
          planned_quantity: 200,
        })
      )
    })
  })

  it('should show edit form when edit button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_number: 'WO001',
          material_id: 1,
          order_type: 'PRODUCTION',
          order_status: 'PLANNED',
          planned_quantity: 100,
          actual_quantity: 0,
          priority: 5,
          created_by_user_id: 1,
          created_at: '2025-11-09T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('WO001')).toBeInTheDocument()
    })

    const editButton = screen.getByRole('button', { name: /edit/i })
    await user.click(editButton)

    expect(screen.getByRole('button', { name: /update work order/i })).toBeInTheDocument()
  })

  it('should delete work order when delete button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_number: 'WO001',
          material_id: 1,
          order_type: 'PRODUCTION',
          order_status: 'PLANNED',
          planned_quantity: 100,
          actual_quantity: 0,
          priority: 5,
          created_by_user_id: 1,
          created_at: '2025-11-09T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    })

    vi.mocked(workOrderService.delete).mockResolvedValue(undefined)

    // Mock window.confirm
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('WO001')).toBeInTheDocument()
    })

    const deleteButton = screen.getByRole('button', { name: /delete/i })
    await user.click(deleteButton)

    await waitFor(() => {
      expect(workOrderService.delete).toHaveBeenCalledWith(1)
    })

    confirmSpy.mockRestore()
  })

  it('should filter work orders by status', async () => {
    const user = userEvent.setup()
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    const statusFilter = screen.getByRole('combobox', { name: /status/i })
    await user.selectOptions(statusFilter, 'IN_PROGRESS')

    await waitFor(() => {
      expect(workOrderService.getAll).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'IN_PROGRESS',
        })
      )
    })
  })

  it('should display pagination when there are multiple pages', async () => {
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: Array(50).fill(null).map((_, i) => ({
        id: i + 1,
        organization_id: 1,
        plant_id: 1,
        work_order_number: `WO${String(i + 1).padStart(3, '0')}`,
        material_id: 1,
        order_type: 'PRODUCTION' as const,
        order_status: 'PLANNED' as const,
        planned_quantity: 100,
        actual_quantity: 0,
        priority: 5,
        created_by_user_id: 1,
        created_at: '2025-11-09T00:00:00Z',
      })),
      total: 100,
      page: 1,
      page_size: 50,
      total_pages: 2,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText(/page 1 of 2/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument()
  })

  it('should handle pagination navigation', async () => {
    const user = userEvent.setup()
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [],
      total: 100,
      page: 1,
      page_size: 50,
      total_pages: 2,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument()
    })

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    await waitFor(() => {
      expect(workOrderService.getAll).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
        })
      )
    })
  })

  it('should close form when cancel button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    // Open form
    await user.click(screen.getByRole('button', { name: /create/i }))
    expect(screen.getByLabelText(/material id/i)).toBeInTheDocument()

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    // Form should be hidden
    await waitFor(() => {
      expect(screen.queryByLabelText(/material id/i)).not.toBeInTheDocument()
    })
  })

  it('should display loading state', () => {
    vi.mocked(workOrderService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('should display empty state when no work orders', async () => {
    vi.mocked(workOrderService.getAll).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })

    render(<WorkOrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText(/no work orders found/i)).toBeInTheDocument()
    })
  })
})
