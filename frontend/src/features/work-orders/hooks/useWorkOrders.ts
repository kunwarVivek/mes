/**
 * useWorkOrders Hook
 *
 * TanStack Query hook for fetching work orders list
 */
import { useQuery } from '@tanstack/react-query'
import { workOrderService, type WorkOrderListParams } from '../services/work-order.service'

export const WORK_ORDERS_QUERY_KEY = 'work-orders'

export function useWorkOrders(params?: WorkOrderListParams) {
  return useQuery({
    queryKey: [WORK_ORDERS_QUERY_KEY, params],
    queryFn: () => workOrderService.list(params),
  })
}
