/**
 * useCompleteWorkOrder Hook
 *
 * TanStack Query mutation hook for completing work orders (IN_PROGRESS -> COMPLETED)
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { workOrderService } from '../services/workOrder.service'
import { WORK_ORDERS_QUERY_KEY } from './useWorkOrders'

export function useCompleteWorkOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => workOrderService.complete(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY, id] })
    },
  })
}
