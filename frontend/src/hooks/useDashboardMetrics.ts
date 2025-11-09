/**
 * useDashboardMetrics Hook
 *
 * Custom hook that fetches data from materials, work orders, and NCRs services in parallel
 * and calculates dashboard metrics
 */
import { useQueries } from '@tanstack/react-query'
import { materialService } from '@/features/materials/services/material.service'
import { workOrderService } from '@/features/work-orders/services/work-order.service'
import { ncrService } from '@/features/quality/services/ncr.service'
import type { Material } from '@/features/materials/services/material.service'
import type { WorkOrder, OrderStatus } from '@/features/work-orders/schemas/work-order.schema'
import type { NCR, NCRStatus } from '@/features/quality/schemas/ncr.schema'

export interface DashboardMetrics {
  totalMaterials: number
  totalWorkOrders: number
  workOrdersByStatus: Record<OrderStatus, number>
  totalNCRs: number
  ncrsByStatus: Record<NCRStatus, number>
}

export interface UseDashboardMetricsResult {
  materials?: Material[]
  workOrders?: WorkOrder[]
  ncrs?: NCR[]
  isLoading: boolean
  error?: Error | null
  metrics?: DashboardMetrics
}

export function useDashboardMetrics(): UseDashboardMetricsResult {
  const queries = useQueries({
    queries: [
      {
        queryKey: ['materials', { page: 1, page_size: 100 }],
        queryFn: () => materialService.list({ page: 1, page_size: 100 }),
      },
      {
        queryKey: ['work-orders', { page: 1, page_size: 100 }],
        queryFn: () => workOrderService.list({ page: 1, page_size: 100 }),
      },
      {
        queryKey: ['ncrs', { page: 1, page_size: 100 }],
        queryFn: () => ncrService.list({ page: 1, page_size: 100 }),
      },
    ],
  })

  const [materialsQuery, workOrdersQuery, ncrsQuery] = queries

  // Check loading state
  const isLoading = queries.some(query => query.isLoading)

  // Check error state
  const error = queries.find(query => query.error)?.error as Error | undefined

  // Extract data
  const materials = materialsQuery.data?.items
  const workOrders = workOrdersQuery.data?.items
  const ncrs = ncrsQuery.data?.items

  // Calculate metrics only when all data is loaded
  const metrics: DashboardMetrics | undefined = materials && workOrders && ncrs
    ? calculateMetrics(materials, workOrders, ncrs)
    : undefined

  return {
    materials,
    workOrders,
    ncrs,
    isLoading,
    error: error || null,
    metrics,
  }
}

function calculateMetrics(
  materials: Material[],
  workOrders: WorkOrder[],
  ncrs: NCR[]
): DashboardMetrics {
  // Count work orders by status
  const workOrdersByStatus: Record<OrderStatus, number> = {
    PLANNED: 0,
    RELEASED: 0,
    IN_PROGRESS: 0,
    COMPLETED: 0,
    CANCELLED: 0,
  }

  workOrders.forEach(wo => {
    const status = wo.order_status as OrderStatus
    if (status in workOrdersByStatus) {
      workOrdersByStatus[status]++
    }
  })

  // Count NCRs by status
  const ncrsByStatus: Record<NCRStatus, number> = {
    OPEN: 0,
    IN_REVIEW: 0,
    RESOLVED: 0,
    CLOSED: 0,
  }

  ncrs.forEach(ncr => {
    const status = ncr.status as NCRStatus
    if (status in ncrsByStatus) {
      ncrsByStatus[status]++
    }
  })

  return {
    totalMaterials: materials.length,
    totalWorkOrders: workOrders.length,
    workOrdersByStatus,
    totalNCRs: ncrs.length,
    ncrsByStatus,
  }
}
