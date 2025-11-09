/**
 * useScheduledOperation Hook
 *
 * TanStack Query hook for fetching single scheduled operation
 */
import { useQuery } from '@tanstack/react-query'
import { schedulingService } from '../services/scheduling.service'
import { SCHEDULED_OPERATIONS_QUERY_KEY } from './useScheduledOperations'

export function useScheduledOperation(id: number) {
  return useQuery({
    queryKey: [SCHEDULED_OPERATIONS_QUERY_KEY, id],
    queryFn: () => schedulingService.getById(id),
    enabled: !!id,
  })
}
