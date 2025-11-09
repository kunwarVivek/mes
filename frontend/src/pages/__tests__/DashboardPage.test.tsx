/**
 * DashboardPage Component Tests
 *
 * TDD Tests for Executive Dashboard page with KPIs and charts
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { DashboardPage } from '../DashboardPage'

// Mock the hook
vi.mock('@/hooks/useDashboardMetrics', () => ({
  useDashboardMetrics: vi.fn(),
}))

// Mock recharts to avoid canvas rendering issues
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div data-testid="bar" />,
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
}))

import { useDashboardMetrics } from '@/hooks/useDashboardMetrics'
import type { DashboardMetrics } from '@/hooks/useDashboardMetrics'
import type { Material } from '@/features/materials/services/material.service'
import type { WorkOrder } from '@/features/work-orders/schemas/work-order.schema'
import type { NCR } from '@/features/quality/schemas/ncr.schema'

const mockUseDashboardMetrics = vi.mocked(useDashboardMetrics)

describe('DashboardPage', () => {
  const mockMaterials: Material[] = [
    {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      material_number: 'MAT-001',
      material_name: 'Widget A',
      material_category_id: 1,
      base_uom_id: 1,
      procurement_type: 'MAKE',
      mrp_type: 'PD',
      safety_stock: 100,
      reorder_point: 200,
      lot_size: 500,
      lead_time_days: 7,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 2,
      organization_id: 1,
      plant_id: 1,
      material_number: 'MAT-002',
      material_name: 'Widget B',
      material_category_id: 1,
      base_uom_id: 1,
      procurement_type: 'BUY',
      mrp_type: 'PD',
      safety_stock: 50,
      reorder_point: 100,
      lot_size: 250,
      lead_time_days: 14,
      is_active: true,
      created_at: '2025-01-02T00:00:00Z',
    },
  ]

  const mockWorkOrders: WorkOrder[] = [
    {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-001',
      material_id: 1,
      order_type: 'PRODUCTION',
      order_status: 'PLANNED',
      planned_quantity: 1000,
      actual_quantity: 0,
      priority: 5,
      created_by_user_id: 1,
      created_at: new Date('2025-01-01'),
      operations: [],
      materials: [],
    },
    {
      id: 2,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-002',
      material_id: 1,
      order_type: 'PRODUCTION',
      order_status: 'RELEASED',
      planned_quantity: 500,
      actual_quantity: 0,
      priority: 7,
      created_by_user_id: 1,
      created_at: new Date('2025-01-02'),
      operations: [],
      materials: [],
    },
    {
      id: 3,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-003',
      material_id: 2,
      order_type: 'PRODUCTION',
      order_status: 'IN_PROGRESS',
      planned_quantity: 750,
      actual_quantity: 500,
      priority: 8,
      created_by_user_id: 1,
      created_at: new Date('2025-01-03'),
      operations: [],
      materials: [],
    },
  ]

  const mockNCRs: NCR[] = [
    {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      ncr_number: 'NCR-001',
      work_order_id: 1,
      material_id: 1,
      defect_type: 'DIMENSIONAL',
      defect_description: 'Out of spec',
      quantity_defective: 10,
      status: 'OPEN',
      reported_by_user_id: 1,
      created_at: new Date('2025-01-01'),
    },
    {
      id: 2,
      organization_id: 1,
      plant_id: 1,
      ncr_number: 'NCR-002',
      work_order_id: 2,
      material_id: 1,
      defect_type: 'VISUAL',
      defect_description: 'Surface defect',
      quantity_defective: 5,
      status: 'IN_REVIEW',
      reported_by_user_id: 1,
      created_at: new Date('2025-01-02'),
    },
  ]

  const mockMetrics: DashboardMetrics = {
    totalMaterials: 2,
    totalWorkOrders: 3,
    workOrdersByStatus: {
      PLANNED: 1,
      RELEASED: 1,
      IN_PROGRESS: 1,
      COMPLETED: 0,
      CANCELLED: 0,
    },
    totalNCRs: 2,
    ncrsByStatus: {
      OPEN: 1,
      IN_REVIEW: 1,
      RESOLVED: 0,
      CLOSED: 0,
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('RED: Initial failing tests', () => {
    it('should render page title', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      render(<DashboardPage />)
      expect(screen.getByText('Executive Dashboard')).toBeInTheDocument()
    })

    it('should render 3 KPI metric cards', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      render(<DashboardPage />)

      // Check for metric card titles
      expect(screen.getByText('Total Materials')).toBeInTheDocument()
      expect(screen.getByText('Total Work Orders')).toBeInTheDocument()
      expect(screen.getByText('Total NCRs')).toBeInTheDocument()
    })

    it('should display correct metric values', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      render(<DashboardPage />)

      // Check for all metric values (using getAllByText since we have duplicate "2")
      const twoElements = screen.getAllByText('2')
      expect(twoElements.length).toBeGreaterThanOrEqual(2) // Materials and NCRs both = 2
      expect(screen.getByText('3')).toBeInTheDocument() // Total work orders
    })

    it('should render work orders chart', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      render(<DashboardPage />)

      expect(screen.getByText('Work Orders by Status')).toBeInTheDocument()
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })

    it('should render NCRs chart', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      render(<DashboardPage />)

      expect(screen.getByText('NCRs by Status')).toBeInTheDocument()
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
    })

    it('should show loading skeleton when loading', () => {
      mockUseDashboardMetrics.mockReturnValue({
        isLoading: true,
        error: null,
      })

      render(<DashboardPage />)

      // Should show skeleton cards
      const skeletons = screen.getAllByTestId('skeleton')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('should show error banner on error', () => {
      mockUseDashboardMetrics.mockReturnValue({
        isLoading: false,
        error: new Error('Failed to fetch data'),
      })

      render(<DashboardPage />)

      expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument()
    })

    it('should have retry button in error state', async () => {
      mockUseDashboardMetrics.mockReturnValue({
        isLoading: false,
        error: new Error('Failed to fetch data'),
      })

      render(<DashboardPage />)

      const retryButton = screen.getByRole('button', { name: /retry/i })
      expect(retryButton).toBeInTheDocument()
    })

    it('should use MetricCard component for KPIs', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      const { container } = render(<DashboardPage />)

      // MetricCards should have their characteristic structure
      // Check that cards exist (they use the card class)
      const cards = container.querySelectorAll('.rounded-xl.border.bg-card')
      expect(cards.length).toBeGreaterThanOrEqual(3)
    })

    it('should have responsive grid layout for KPI cards', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      const { container } = render(<DashboardPage />)

      // Check for grid classes
      const gridElements = container.querySelectorAll('[class*="grid"]')
      expect(gridElements.length).toBeGreaterThan(0)
    })

    it('should display icons for each KPI card', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      const { container } = render(<DashboardPage />)

      // Check for SVG icons (lucide-react renders SVGs)
      const icons = container.querySelectorAll('svg')
      expect(icons.length).toBeGreaterThan(0)
    })

    it('should handle zero metrics gracefully', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: [],
        workOrders: [],
        ncrs: [],
        isLoading: false,
        error: null,
        metrics: {
          totalMaterials: 0,
          totalWorkOrders: 0,
          workOrdersByStatus: {
            PLANNED: 0,
            RELEASED: 0,
            IN_PROGRESS: 0,
            COMPLETED: 0,
            CANCELLED: 0,
          },
          totalNCRs: 0,
          ncrsByStatus: {
            OPEN: 0,
            IN_REVIEW: 0,
            RESOLVED: 0,
            CLOSED: 0,
          },
        },
      })

      render(<DashboardPage />)

      // Should still render the structure
      expect(screen.getByText('Executive Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Total Materials')).toBeInTheDocument()
    })

    it('should render charts section with proper layout', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      const { container } = render(<DashboardPage />)

      // Should have chart containers
      expect(screen.getByText('Work Orders by Status')).toBeInTheDocument()
      expect(screen.getByText('NCRs by Status')).toBeInTheDocument()
    })

    it('should show all work order statuses in chart', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      render(<DashboardPage />)

      // Bar chart should show data for all statuses
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })

    it('should show all NCR statuses in chart', () => {
      mockUseDashboardMetrics.mockReturnValue({
        materials: mockMaterials,
        workOrders: mockWorkOrders,
        ncrs: mockNCRs,
        isLoading: false,
        error: null,
        metrics: mockMetrics,
      })

      render(<DashboardPage />)

      // Pie chart should show data for all statuses
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
    })
  })
})
