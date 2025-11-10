/**
 * useDashboardMetrics Hook
 *
 * Custom hook that fetches aggregated dashboard metrics from backend
 * Uses /api/v1/metrics/dashboard endpoint (not limited by pagination)
 */
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api-client'
import type { OrderStatus } from '@/features/work-orders/schemas/work-order.schema'
import type { NCRStatus } from '@/features/quality/schemas/ncr.schema'

export interface DashboardMetrics {
  totalMaterials: number
  totalWorkOrders: number
  workOrdersByStatus: Record<OrderStatus, number>
  totalNCRs: number
  ncrsByStatus: Record<NCRStatus, number>
}

export interface UseDashboardMetricsResult {
  isLoading: boolean
  error?: Error | null
  metrics?: DashboardMetrics
}

interface DashboardMetricsResponse {
  materials_count: number
  work_orders_count: number
  work_orders_by_status: Record<string, number>
  ncrs_count: number
  ncrs_by_status: Record<string, number>
}

export function useDashboardMetrics(): UseDashboardMetricsResult {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => {
      const response = await apiClient.get<DashboardMetricsResponse>('/api/v1/metrics/dashboard')
      return response.data
    },
  })

  // Transform snake_case API response to camelCase
  const metrics: DashboardMetrics | undefined = data
    ? {
        totalMaterials: data.materials_count,
        totalWorkOrders: data.work_orders_count,
        workOrdersByStatus: data.work_orders_by_status as Record<OrderStatus, number>,
        totalNCRs: data.ncrs_count,
        ncrsByStatus: data.ncrs_by_status as Record<NCRStatus, number>,
      }
    : undefined

  return {
    isLoading,
    error: error as Error | null | undefined,
    metrics,
  }
}
