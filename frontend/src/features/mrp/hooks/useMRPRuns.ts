/**
 * useMRPRuns Hook
 *
 * TanStack Query hook for fetching MRP runs list
 */
import { useQuery } from '@tanstack/react-query'
import { mrpService } from '../services/mrp.service'
import type { MRPRunFilters } from '../types/mrp.types'

export const MRP_RUNS_QUERY_KEY = 'mrp-runs'

export function useMRPRuns(filters?: MRPRunFilters) {
  return useQuery({
    queryKey: [MRP_RUNS_QUERY_KEY, filters],
    queryFn: () => mrpService.getAll(filters),
  })
}
