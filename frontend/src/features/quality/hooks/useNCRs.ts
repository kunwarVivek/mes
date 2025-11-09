/**
 * useNCRs Hook
 *
 * TanStack Query hook for fetching NCRs list
 */
import { useQuery } from '@tanstack/react-query'
import { ncrService, type NCRListParams } from '../services/ncr.service'

export function useNCRs(params?: NCRListParams) {
  return useQuery({
    queryKey: ['ncrs', params],
    queryFn: () => ncrService.list(params),
  })
}
