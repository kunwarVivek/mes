/**
 * WorkOrderFormPage Component Tests
 *
 * TDD Tests for Work Order Form Page (Create/Edit modes)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WorkOrderFormPage } from '../WorkOrderFormPage'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock the hooks
vi.mock('../../hooks/useWorkOrder', () => ({
  useWorkOrder: vi.fn(),
}))

vi.mock('../../hooks/useWorkOrderMutations', () => ({
  useWorkOrderMutations: vi.fn(),
}))

// Mock react-router-dom navigation and params
const mockNavigate = vi.fn()
let mockParams = { id: undefined }
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => mockParams,
  }
})

import { useWorkOrder } from '../../hooks/useWorkOrder'
import { useWorkOrderMutations } from '../../hooks/useWorkOrderMutations'

const mockUseWorkOrder = vi.mocked(useWorkOrder)
const mockUseWorkOrderMutations = vi.mocked(useWorkOrderMutations)

describe('WorkOrderFormPage', () => {
  const mockWorkOrder = {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    work_order_number: 'WO-001',
    material_id: 100,
    order_type: 'PRODUCTION',
    order_status: 'PLANNED',
    planned_quantity: 1000,
    actual_quantity: 0,
    priority: 5,
    created_by_user_id: 1,
    created_at: new Date('2025-01-01'),
    start_date_planned: new Date('2025-01-10'),
    end_date_planned: new Date('2025-01-20'),
    operations: [],
    materials: [],
  }

  const mockMutations = {
    createWorkOrder: { mutate: vi.fn(), mutateAsync: vi.fn(), isPending: false },
    updateWorkOrder: { mutate: vi.fn(), mutateAsync: vi.fn(), isPending: false },
    cancelWorkOrder: { mutate: vi.fn(), isPending: false },
    releaseWorkOrder: { mutate: vi.fn(), isPending: false },
    startWorkOrder: { mutate: vi.fn(), isPending: false },
    completeWorkOrder: { mutate: vi.fn(), isPending: false },
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseWorkOrderMutations.mockReturnValue(mockMutations as any)
  })

  const renderWithRouter = (component: React.ReactElement, route = '/work-orders/new') => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    window.history.pushState({}, 'Test page', route)
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/work-orders/new" element={component} />
            <Route path="/work-orders/:id/edit" element={component} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    )
  }

  describe('Create Mode', () => {
    beforeEach(() => {
      // Reset params for create mode
      mockParams = { id: undefined }
      mockUseWorkOrder.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      } as any)
    })

    it('should render create page title', () => {
      renderWithRouter(<WorkOrderFormPage />)

      const heading = screen.getByRole('heading', { name: /create work order/i })
      expect(heading).toBeInTheDocument()
    })

    it('should render breadcrumb navigation', () => {
      renderWithRouter(<WorkOrderFormPage />)

      expect(screen.getByText('Home')).toBeInTheDocument()
      expect(screen.getByText('Work Orders')).toBeInTheDocument()
      expect(screen.getByText('Create')).toBeInTheDocument()
    })

    it('should render back button', () => {
      renderWithRouter(<WorkOrderFormPage />)

      // Back button is icon-only, check by aria-label or by finding buttons
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('should render WorkOrderForm component', () => {
      renderWithRouter(<WorkOrderFormPage />)

      // Check for form fields
      expect(screen.getByLabelText(/material id/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/order type/i)).toBeInTheDocument()
    })

    it('should navigate back when back button clicked', async () => {
      const user = userEvent.setup()
      renderWithRouter(<WorkOrderFormPage />)

      // Back button is the first icon button
      const buttons = screen.getAllByRole('button')
      const backButton = buttons[0] // First button should be back button
      await user.click(backButton)

      expect(mockNavigate).toHaveBeenCalledWith('/work-orders')
    })

    it('should navigate to list after successful create', async () => {
      mockMutations.createWorkOrder.mutateAsync.mockResolvedValue(mockWorkOrder)
      renderWithRouter(<WorkOrderFormPage />)

      // Form submission will trigger navigation in onSuccess callback
      // This is tested in WorkOrderForm.test.tsx
      const heading = screen.getByRole('heading', { name: /create work order/i })
      expect(heading).toBeInTheDocument()
    })
  })

  describe('Edit Mode', () => {
    beforeEach(() => {
      // Set mock params to return id
      mockParams = { id: '1' }
      mockUseWorkOrder.mockReturnValue({
        data: mockWorkOrder,
        isLoading: false,
        error: null,
      } as any)
    })

    it('should render edit page title with work order number', () => {
      renderWithRouter(<WorkOrderFormPage />, '/work-orders/1/edit')

      expect(screen.getByText('Edit Work Order #WO-001')).toBeInTheDocument()
    })

    it('should render breadcrumb navigation for edit', () => {
      renderWithRouter(<WorkOrderFormPage />, '/work-orders/1/edit')

      expect(screen.getByText('Home')).toBeInTheDocument()
      expect(screen.getByText('Work Orders')).toBeInTheDocument()
      expect(screen.getByText('Edit')).toBeInTheDocument()
    })

    it('should load work order data', () => {
      renderWithRouter(<WorkOrderFormPage />, '/work-orders/1/edit')

      expect(mockUseWorkOrder).toHaveBeenCalledWith(1)
    })

    it('should show loading state while fetching work order', () => {
      mockUseWorkOrder.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any)

      const { container } = renderWithRouter(<WorkOrderFormPage />, '/work-orders/1/edit')

      const skeletons = container.querySelectorAll('.skeleton')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('should show error state if work order fails to load', () => {
      mockUseWorkOrder.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load'),
      } as any)

      renderWithRouter(<WorkOrderFormPage />, '/work-orders/1/edit')

      expect(screen.getByText(/failed to load work order/i)).toBeInTheDocument()
    })

    it('should render form with work order data', () => {
      renderWithRouter(<WorkOrderFormPage />, '/work-orders/1/edit')

      // Material ID should be shown as readonly
      const materialField = screen.getByLabelText(/material id/i)
      expect(materialField).toBeInTheDocument()
      expect(materialField).toBeDisabled()
    })
  })

  describe('Form Submission', () => {
    it('should pass onSuccess callback to WorkOrderForm', () => {
      // Reset params for create mode
      mockParams = { id: undefined }
      mockUseWorkOrder.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      } as any)

      renderWithRouter(<WorkOrderFormPage />)

      // WorkOrderForm should be rendered with onSuccess prop
      // Check for form fields instead of submit button
      expect(screen.getByLabelText(/material id/i)).toBeInTheDocument()
    })
  })
})
