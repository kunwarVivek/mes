/**
 * useBOMs Hook
 *
 * TanStack Query hook for fetching BOMs list
 */
import { useQuery } from '@tanstack/react-query'
import { bomService } from '../services/bom.service'
import type { BOMFilters } from '../types/bom.types'

export const BOMS_QUERY_KEY = 'boms'

export function useBOMs(filters?: BOMFilters) {
  return useQuery({
    queryKey: [BOMS_QUERY_KEY, filters],
    queryFn: () => bomService.getAll(filters),
  })
}
