/**
 * useBOM Hook
 *
 * TanStack Query hook for fetching a single BOM by ID
 */
import { useQuery } from '@tanstack/react-query'
import { bomService } from '../services/bom.service'
import { BOMS_QUERY_KEY } from './useBOMs'

export function useBOM(id: number) {
  return useQuery({
    queryKey: [BOMS_QUERY_KEY, id],
    queryFn: () => bomService.getById(id),
    enabled: !!id,
  })
}
