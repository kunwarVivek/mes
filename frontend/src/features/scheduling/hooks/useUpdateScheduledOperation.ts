/**
 * useUpdateScheduledOperation Hook
 *
 * TanStack Query mutation hook for updating scheduled operations
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { schedulingService } from '../services/scheduling.service'
import { SCHEDULED_OPERATIONS_QUERY_KEY } from './useScheduledOperations'
import type { UpdateScheduledOperationDTO } from '../types/scheduling.types'

export function useUpdateScheduledOperation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateScheduledOperationDTO }) =>
      schedulingService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [SCHEDULED_OPERATIONS_QUERY_KEY] })
    },
  })
}
