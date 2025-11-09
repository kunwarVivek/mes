/**
 * useDashboardMetrics Hook Tests
 *
 * TDD Tests for Executive Dashboard metrics aggregation hook
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useDashboardMetrics } from '../useDashboardMetrics'
import { materialService } from '@/features/materials/services/material.service'
import { workOrderService } from '@/features/work-orders/services/work-order.service'
import { ncrService } from '@/features/quality/services/ncr.service'
import type { Material } from '@/features/materials/services/material.service'
import type { WorkOrder } from '@/features/work-orders/schemas/work-order.schema'
import type { NCR } from '@/features/quality/schemas/ncr.schema'

// Mock services
vi.mock('@/features/materials/services/material.service', () => ({
  materialService: {
    list: vi.fn(),
  },
}))

vi.mock('@/features/work-orders/services/work-order.service', () => ({
  workOrderService: {
    list: vi.fn(),
  },
}))

vi.mock('@/features/quality/services/ncr.service', () => ({
  ncrService: {
    list: vi.fn(),
  },
}))

const mockMaterialService = vi.mocked(materialService)
const mockWorkOrderService = vi.mocked(workOrderService)
const mockNCRService = vi.mocked(ncrService)

describe('useDashboardMetrics', () => {
  let queryClient: QueryClient

  const createWrapper = () => {
    const TestWrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    return TestWrapper
  }

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
    vi.clearAllMocks()
  })

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
    {
      id: 4,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-004',
      material_id: 2,
      order_type: 'PRODUCTION',
      order_status: 'COMPLETED',
      planned_quantity: 1000,
      actual_quantity: 1000,
      priority: 5,
      created_by_user_id: 1,
      created_at: new Date('2025-01-04'),
      operations: [],
      materials: [],
    },
    {
      id: 5,
      organization_id: 1,
      plant_id: 1,
      work_order_number: 'WO-005',
      material_id: 1,
      order_type: 'PRODUCTION',
      order_status: 'CANCELLED',
      planned_quantity: 200,
      actual_quantity: 0,
      priority: 3,
      created_by_user_id: 1,
      created_at: new Date('2025-01-05'),
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
    {
      id: 3,
      organization_id: 1,
      plant_id: 1,
      ncr_number: 'NCR-003',
      work_order_id: 3,
      material_id: 2,
      defect_type: 'FUNCTIONAL',
      defect_description: 'Not working',
      quantity_defective: 3,
      status: 'RESOLVED',
      reported_by_user_id: 1,
      resolved_by_user_id: 2,
      resolved_at: new Date('2025-01-10'),
      resolution_notes: 'Fixed',
      created_at: new Date('2025-01-03'),
    },
    {
      id: 4,
      organization_id: 1,
      plant_id: 1,
      ncr_number: 'NCR-004',
      work_order_id: 4,
      material_id: 2,
      defect_type: 'MATERIAL',
      defect_description: 'Wrong material',
      quantity_defective: 15,
      status: 'CLOSED',
      reported_by_user_id: 1,
      resolved_by_user_id: 2,
      resolved_at: new Date('2025-01-11'),
      resolution_notes: 'Replaced',
      created_at: new Date('2025-01-04'),
    },
  ]

  describe('RED: Initial failing tests', () => {
    it('should return loading state initially', () => {
      mockMaterialService.list.mockReturnValue(new Promise(() => {}))
      mockWorkOrderService.list.mockReturnValue(new Promise(() => {}))
      mockNCRService.list.mockReturnValue(new Promise(() => {}))

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.materials).toBeUndefined()
      expect(result.current.workOrders).toBeUndefined()
      expect(result.current.ncrs).toBeUndefined()
      expect(result.current.metrics).toBeUndefined()
    })

    it('should fetch data from all three services in parallel', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: mockMaterials,
        total: 2,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: mockWorkOrders,
        total: 5,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockNCRService.list.mockResolvedValue({
        items: mockNCRs,
        total: 4,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(mockMaterialService.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
      })
      expect(mockWorkOrderService.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
      })
      expect(mockNCRService.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
      })
    })

    it('should return materials data', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: mockMaterials,
        total: 2,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 0,
      })
      mockNCRService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.materials).toEqual(mockMaterials)
    })

    it('should return work orders data', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: mockWorkOrders,
        total: 5,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockNCRService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.workOrders).toEqual(mockWorkOrders)
    })

    it('should return NCRs data', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 0,
      })
      mockNCRService.list.mockResolvedValue({
        items: mockNCRs,
        total: 4,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.ncrs).toEqual(mockNCRs)
    })

    it('should calculate total materials count', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: mockMaterials,
        total: 2,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 0,
      })
      mockNCRService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.metrics?.totalMaterials).toBe(2)
    })

    it('should calculate total work orders count', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: mockWorkOrders,
        total: 5,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockNCRService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.metrics?.totalWorkOrders).toBe(5)
    })

    it('should calculate work orders by status', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: mockWorkOrders,
        total: 5,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockNCRService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.metrics?.workOrdersByStatus).toEqual({
        PLANNED: 1,
        RELEASED: 1,
        IN_PROGRESS: 1,
        COMPLETED: 1,
        CANCELLED: 1,
      })
    })

    it('should calculate total NCRs count', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 0,
      })
      mockNCRService.list.mockResolvedValue({
        items: mockNCRs,
        total: 4,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.metrics?.totalNCRs).toBe(4)
    })

    it('should calculate NCRs by status', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 0,
      })
      mockNCRService.list.mockResolvedValue({
        items: mockNCRs,
        total: 4,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.metrics?.ncrsByStatus).toEqual({
        OPEN: 1,
        IN_REVIEW: 1,
        RESOLVED: 1,
        CLOSED: 1,
      })
    })

    it('should handle errors from material service', async () => {
      mockMaterialService.list.mockRejectedValue(new Error('Materials fetch failed'))
      mockWorkOrderService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 0,
      })
      mockNCRService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
    })

    it('should handle errors from work order service', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockRejectedValue(new Error('Work orders fetch failed'))
      mockNCRService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
    })

    it('should handle errors from NCR service', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 0,
      })
      mockNCRService.list.mockRejectedValue(new Error('NCRs fetch failed'))

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
    })

    it('should handle empty data gracefully', async () => {
      mockMaterialService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })
      mockWorkOrderService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 0,
      })
      mockNCRService.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        total_pages: 1,
      })

      const { result } = renderHook(() => useDashboardMetrics(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.metrics).toEqual({
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
      })
    })
  })
})
