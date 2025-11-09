/**
 * useUpdateWorkOrder Hook
 *
 * TanStack Query mutation hook for updating work orders
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { workOrderService } from '../services/workOrder.service'
import { WORK_ORDERS_QUERY_KEY } from './useWorkOrders'
import type { UpdateWorkOrderDTO } from '../types/workOrder.types'

interface UpdateWorkOrderParams extends UpdateWorkOrderDTO {
  id: number
}

export function useUpdateWorkOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateWorkOrderParams) =>
      workOrderService.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY, variables.id] })
    },
  })
}
