/**
 * useStartWorkOrder Hook
 *
 * TanStack Query mutation hook for starting work orders (RELEASED -> IN_PROGRESS)
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { workOrderService } from '../services/workOrder.service'
import { WORK_ORDERS_QUERY_KEY } from './useWorkOrders'

export function useStartWorkOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => workOrderService.start(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY, id] })
    },
  })
}
