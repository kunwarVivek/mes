/**
 * useNCR Hook
 *
 * TanStack Query hook for fetching single NCR
 */
import { useQuery } from '@tanstack/react-query'
import { ncrService } from '../services/ncr.service'

export const NCR_QUERY_KEY = 'ncr'

export function useNCR(id: number) {
  return useQuery({
    queryKey: [NCR_QUERY_KEY, id],
    queryFn: () => ncrService.getById(id),
    enabled: !!id,
  })
}
