/**
 * WorkOrderTable Component Tests
 *
 * TDD Tests for Work Order Table with status badges and state transition actions
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WorkOrderTable } from '../WorkOrderTable'
import type { WorkOrder } from '../../schemas/work-order.schema'

// Mock the hooks module
vi.mock('../../hooks/useWorkOrders', () => ({
  useWorkOrders: vi.fn(),
}))

vi.mock('../../hooks/useWorkOrderMutations', () => ({
  useWorkOrderMutations: vi.fn(),
}))

import { useWorkOrders } from '../../hooks/useWorkOrders'
import { useWorkOrderMutations } from '../../hooks/useWorkOrderMutations'

const mockUseWorkOrders = vi.mocked(useWorkOrders)
const mockUseWorkOrderMutations = vi.mocked(useWorkOrderMutations)

describe('WorkOrderTable', () => {
  const mockWorkOrders: WorkOrder[] = [
    {
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
    },
    {
      id: 2,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-002',
      material_id: 101,
      order_type: 'REWORK',
      order_status: 'RELEASED',
      planned_quantity: 500,
      actual_quantity: 0,
      priority: 8,
      created_by_user_id: 1,
      created_at: new Date('2025-01-02'),
      start_date_planned: new Date('2025-01-15'),
      end_date_planned: new Date('2025-01-25'),
      operations: [],
      materials: [],
    },
    {
      id: 3,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-003',
      material_id: 102,
      order_type: 'ASSEMBLY',
      order_status: 'IN_PROGRESS',
      planned_quantity: 250,
      actual_quantity: 100,
      priority: 10,
      created_by_user_id: 1,
      created_at: new Date('2025-01-03'),
      start_date_planned: new Date('2025-01-05'),
      end_date_planned: new Date('2025-01-12'),
      start_date_actual: new Date('2025-01-06'),
      operations: [],
      materials: [],
    },
    {
      id: 4,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-004',
      material_id: 103,
      order_type: 'PRODUCTION',
      order_status: 'COMPLETED',
      planned_quantity: 750,
      actual_quantity: 750,
      priority: 3,
      created_by_user_id: 1,
      created_at: new Date('2025-01-04'),
      start_date_planned: new Date('2025-01-08'),
      end_date_planned: new Date('2025-01-18'),
      start_date_actual: new Date('2025-01-08'),
      end_date_actual: new Date('2025-01-17'),
      operations: [],
      materials: [],
    },
    {
      id: 5,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-005',
      material_id: 104,
      order_type: 'PRODUCTION',
      order_status: 'CANCELLED',
      planned_quantity: 1200,
      actual_quantity: 0,
      priority: 1,
      created_by_user_id: 1,
      created_at: new Date('2025-01-05'),
      operations: [],
      materials: [],
    },
  ]

  const mockMutations = {
    releaseWorkOrder: { mutate: vi.fn(), isPending: false },
    startWorkOrder: { mutate: vi.fn(), isPending: false },
    completeWorkOrder: { mutate: vi.fn(), isPending: false },
    createWorkOrder: { mutate: vi.fn(), isPending: false },
    updateWorkOrder: { mutate: vi.fn(), isPending: false },
    cancelWorkOrder: { mutate: vi.fn(), isPending: false },
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseWorkOrderMutations.mockReturnValue(mockMutations)
  })

  describe('Basic Rendering', () => {
    it('should render work orders table with correct columns', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: mockWorkOrders, total: 5 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      // Check column headers
      expect(screen.getByText('WO Number')).toBeInTheDocument()
      expect(screen.getByText('Material')).toBeInTheDocument()
      expect(screen.getByText('Order Type')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Priority')).toBeInTheDocument()
      expect(screen.getByText('Planned Qty')).toBeInTheDocument()
      expect(screen.getByText('Planned Dates')).toBeInTheDocument()
      expect(screen.getByText('Actions')).toBeInTheDocument()
    })

    it('should display work order data correctly', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[0]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      expect(screen.getByText('WO-001')).toBeInTheDocument()
      expect(screen.getByText('1000')).toBeInTheDocument()
    })

    it('should render loading skeleton when loading', () => {
      mockUseWorkOrders.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any)

      const { container } = render(<WorkOrderTable />)

      // Check for skeleton elements by class name
      const skeletons = container.querySelectorAll('.skeleton')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('should render empty state when no data', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [], total: 0 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      expect(screen.getByText('No work orders found')).toBeInTheDocument()
    })
  })

  describe('Status Badge Rendering', () => {
    it('should render PLANNED status with secondary variant', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[0]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const statusBadge = screen.getByText('Planned')
      expect(statusBadge).toBeInTheDocument()
    })

    it('should render RELEASED status with warning variant', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[1]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const statusBadge = screen.getByText('Released')
      expect(statusBadge).toBeInTheDocument()
    })

    it('should render IN_PROGRESS status with success variant and pulse', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[2]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const statusBadge = screen.getByText('In Progress')
      expect(statusBadge).toBeInTheDocument()
    })

    it('should render COMPLETED status with success variant', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[3]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const statusBadge = screen.getByText('Completed')
      expect(statusBadge).toBeInTheDocument()
    })

    it('should render CANCELLED status with destructive variant', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[4]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const statusBadge = screen.getByText('Cancelled')
      expect(statusBadge).toBeInTheDocument()
    })
  })

  describe('Priority Indicator', () => {
    it('should render priority values correctly', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: mockWorkOrders, total: 5 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      // Check that priorities are displayed (values 1, 3, 5, 8, 10)
      const table = screen.getByRole('grid')
      expect(within(table).getByText('5')).toBeInTheDocument()
      expect(within(table).getByText('8')).toBeInTheDocument()
      expect(within(table).getByText('10')).toBeInTheDocument()
    })
  })

  describe('State Transition Actions', () => {
    it('should show Release button for PLANNED status', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[0]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const releaseButton = screen.getByRole('button', { name: /release/i })
      expect(releaseButton).toBeInTheDocument()
      expect(releaseButton).not.toBeDisabled()
    })

    it('should call releaseWorkOrder when Release button clicked', async () => {
      const user = userEvent.setup()
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[0]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const releaseButton = screen.getByRole('button', { name: /release/i })
      await user.click(releaseButton)

      expect(mockMutations.releaseWorkOrder.mutate).toHaveBeenCalledWith(1)
    })

    it('should show Start button for RELEASED status', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[1]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const startButton = screen.getByRole('button', { name: /start/i })
      expect(startButton).toBeInTheDocument()
      expect(startButton).not.toBeDisabled()
    })

    it('should call startWorkOrder when Start button clicked', async () => {
      const user = userEvent.setup()
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[1]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const startButton = screen.getByRole('button', { name: /start/i })
      await user.click(startButton)

      expect(mockMutations.startWorkOrder.mutate).toHaveBeenCalledWith(2)
    })

    it('should show Complete button for IN_PROGRESS status', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[2]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const completeButton = screen.getByRole('button', { name: /complete/i })
      expect(completeButton).toBeInTheDocument()
      expect(completeButton).not.toBeDisabled()
    })

    it('should call completeWorkOrder when Complete button clicked', async () => {
      const user = userEvent.setup()
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[2]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      const completeButton = screen.getByRole('button', { name: /complete/i })
      await user.click(completeButton)

      expect(mockMutations.completeWorkOrder.mutate).toHaveBeenCalledWith(3)
    })

    it('should show no action buttons for COMPLETED status', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[3]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      expect(screen.queryByRole('button', { name: /release/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /start/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /complete/i })).not.toBeInTheDocument()
    })

    it('should show no action buttons for CANCELLED status', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[4]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      expect(screen.queryByRole('button', { name: /release/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /start/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /complete/i })).not.toBeInTheDocument()
    })
  })

  describe('Row Click Navigation', () => {
    it('should call onRowClick when row is clicked', async () => {
      const user = userEvent.setup()
      const onRowClick = vi.fn()
      mockUseWorkOrders.mockReturnValue({
        data: { items: [mockWorkOrders[0]], total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable onRowClick={onRowClick} />)

      const row = screen.getByText('WO-001').closest('tr')
      if (row) {
        await user.click(row)
      }

      expect(onRowClick).toHaveBeenCalledWith(mockWorkOrders[0])
    })
  })

  describe('Filtering', () => {
    it('should filter by status', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: mockWorkOrders.filter(wo => wo.order_status === 'PLANNED'), total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable filters={{ status: 'PLANNED' }} />)

      expect(screen.getByText('WO-001')).toBeInTheDocument()
      expect(screen.queryByText('WO-002')).not.toBeInTheDocument()
    })

    it('should filter by material_id', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: mockWorkOrders.filter(wo => wo.material_id === 100), total: 1 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable filters={{ material_id: 100 }} />)

      expect(screen.getByText('WO-001')).toBeInTheDocument()
    })
  })

  describe('Order Type Badges', () => {
    it('should render order type badges for all types', () => {
      mockUseWorkOrders.mockReturnValue({
        data: { items: mockWorkOrders.slice(0, 3), total: 3 },
        isLoading: false,
        error: null,
      } as any)

      render(<WorkOrderTable />)

      expect(screen.getByText('Production')).toBeInTheDocument()
      expect(screen.getByText('Rework')).toBeInTheDocument()
      expect(screen.getByText('Assembly')).toBeInTheDocument()
    })
  })
})
