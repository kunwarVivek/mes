/**
 * useCreateWorkOrder Hook
 *
 * TanStack Query mutation hook for creating work orders
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { workOrderService } from '../services/workOrder.service'
import { WORK_ORDERS_QUERY_KEY } from './useWorkOrders'
import type { CreateWorkOrderDTO } from '../types/workOrder.types'

export function useCreateWorkOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateWorkOrderDTO) => workOrderService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] })
    },
  })
}
