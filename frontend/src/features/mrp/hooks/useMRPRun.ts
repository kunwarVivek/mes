/**
 * useMRPRun Hook
 *
 * TanStack Query hook for fetching single MRP run
 */
import { useQuery } from '@tanstack/react-query'
import { mrpService } from '../services/mrp.service'
import { MRP_RUNS_QUERY_KEY } from './useMRPRuns'

export function useMRPRun(id: number) {
  return useQuery({
    queryKey: [MRP_RUNS_QUERY_KEY, id],
    queryFn: () => mrpService.getById(id),
    enabled: !!id,
  })
}
