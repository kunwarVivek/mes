/**
 * useWorkOrders Hook
 *
 * TanStack Query hook for fetching work orders list
 */
import { useQuery } from '@tanstack/react-query'
import { workOrderService } from '../services/workOrder.service'
import type { WorkOrderFilters } from '../types/workOrder.types'

export const WORK_ORDERS_QUERY_KEY = 'work-orders'

export function useWorkOrders(filters?: WorkOrderFilters) {
  return useQuery({
    queryKey: [WORK_ORDERS_QUERY_KEY, filters],
    queryFn: () => workOrderService.getAll(filters),
  })
}
