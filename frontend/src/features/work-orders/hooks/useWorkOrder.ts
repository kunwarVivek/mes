/**
 * useWorkOrder Hook
 *
 * TanStack Query hook for fetching a single work order by ID
 */
import { useQuery } from '@tanstack/react-query'
import { workOrderService } from '../services/workOrder.service'
import { WORK_ORDERS_QUERY_KEY } from './useWorkOrders'

export function useWorkOrder(id: number) {
  return useQuery({
    queryKey: [WORK_ORDERS_QUERY_KEY, id],
    queryFn: () => workOrderService.getById(id),
    enabled: !!id,
  })
}
