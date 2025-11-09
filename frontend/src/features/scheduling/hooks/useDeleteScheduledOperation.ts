/**
 * useDeleteScheduledOperation Hook
 *
 * TanStack Query mutation hook for deleting scheduled operations
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { schedulingService } from '../services/scheduling.service'
import { SCHEDULED_OPERATIONS_QUERY_KEY } from './useScheduledOperations'

export function useDeleteScheduledOperation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => schedulingService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [SCHEDULED_OPERATIONS_QUERY_KEY] })
    },
  })
}
