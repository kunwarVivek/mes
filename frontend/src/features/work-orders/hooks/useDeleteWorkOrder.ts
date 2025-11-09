/**
 * useDeleteWorkOrder Hook
 *
 * TanStack Query mutation hook for cancelling work orders
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { workOrderService } from '../services/workOrder.service'
import { WORK_ORDERS_QUERY_KEY } from './useWorkOrders'

export function useDeleteWorkOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => workOrderService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] })
    },
  })
}
