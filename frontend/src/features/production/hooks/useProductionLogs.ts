/**
 * useProductionLogs Hooks
 *
 * TanStack Query hooks for production logging operations
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productionLogService } from '../services/productionLog.service'
import type {
  ProductionLogCreateRequest,
  ProductionLogFilters,
} from '../types/productionLog.types'

export const PRODUCTION_LOGS_QUERY_KEY = 'production-logs'
export const PRODUCTION_SUMMARY_QUERY_KEY = 'production-summary'
export const PRODUCTION_LOG_QUERY_KEY = 'production-log'

/**
 * Fetch production logs for a work order with optional filters
 */
export function useProductionLogs(workOrderId: number, params?: ProductionLogFilters) {
  return useQuery({
    queryKey: [PRODUCTION_LOGS_QUERY_KEY, workOrderId, params],
    queryFn: () => productionLogService.listByWorkOrder(workOrderId, params),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })
}

/**
 * Fetch production summary statistics for a work order
 */
export function useProductionSummary(workOrderId: number) {
  return useQuery({
    queryKey: [PRODUCTION_SUMMARY_QUERY_KEY, workOrderId],
    queryFn: () => productionLogService.getSummary(workOrderId),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })
}

/**
 * Fetch a single production log by ID
 */
export function useProductionLog(logId: number) {
  return useQuery({
    queryKey: [PRODUCTION_LOG_QUERY_KEY, logId],
    queryFn: () => productionLogService.getById(logId),
  })
}

/**
 * Mutation hook for creating production log entries
 */
export function useLogProduction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ProductionLogCreateRequest) => productionLogService.logProduction(data),
    onSuccess: (data) => {
      // Invalidate all queries related to this work order
      queryClient.invalidateQueries({
        queryKey: [PRODUCTION_LOGS_QUERY_KEY, data.work_order_id],
      })
      queryClient.invalidateQueries({
        queryKey: [PRODUCTION_SUMMARY_QUERY_KEY, data.work_order_id],
      })
    },
  })
}
