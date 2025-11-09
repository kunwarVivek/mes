/**
 * useNCR Hook
 *
 * TanStack Query hook for fetching single NCR
 */
import { useQuery } from '@tanstack/react-query'
import { ncrService } from '../services/ncr.service'

export function useNCR(id: number) {
  return useQuery({
    queryKey: ['ncrs', id],
    queryFn: () => ncrService.get(id),
    enabled: !!id,
  })
}
