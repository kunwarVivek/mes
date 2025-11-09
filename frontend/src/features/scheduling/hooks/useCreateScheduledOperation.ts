/**
 * useCreateScheduledOperation Hook
 *
 * TanStack Query mutation hook for creating scheduled operations
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { schedulingService } from '../services/scheduling.service'
import { SCHEDULED_OPERATIONS_QUERY_KEY } from './useScheduledOperations'
import type { CreateScheduledOperationDTO } from '../types/scheduling.types'

export function useCreateScheduledOperation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateScheduledOperationDTO) => schedulingService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [SCHEDULED_OPERATIONS_QUERY_KEY] })
    },
  })
}
