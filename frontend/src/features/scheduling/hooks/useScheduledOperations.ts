/**
 * useScheduledOperations Hook
 *
 * TanStack Query hook for fetching scheduled operations list
 */
import { useQuery } from '@tanstack/react-query'
import { schedulingService } from '../services/scheduling.service'
import type { ScheduledOperationFilters } from '../types/scheduling.types'

export const SCHEDULED_OPERATIONS_QUERY_KEY = 'scheduled-operations'

export function useScheduledOperations(filters?: ScheduledOperationFilters) {
  return useQuery({
    queryKey: [SCHEDULED_OPERATIONS_QUERY_KEY, filters],
    queryFn: () => schedulingService.getAll(filters),
  })
}
