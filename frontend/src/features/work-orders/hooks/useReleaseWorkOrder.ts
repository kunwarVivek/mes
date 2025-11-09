/**
 * useReleaseWorkOrder Hook
 *
 * TanStack Query mutation hook for releasing work orders (PLANNED -> RELEASED)
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { workOrderService } from '../services/workOrder.service'
import { WORK_ORDERS_QUERY_KEY } from './useWorkOrders'

export function useReleaseWorkOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => workOrderService.release(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY, id] })
    },
  })
}
