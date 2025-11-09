/**
 * useMaterials Hook
 *
 * TanStack Query hook for fetching materials list
 */
import { useQuery } from '@tanstack/react-query'
import { materialService } from '../services/material.service'
import type { MaterialFilters } from '../types/material.types'

export const MATERIALS_QUERY_KEY = 'materials'

export function useMaterials(filters?: MaterialFilters) {
  return useQuery({
    queryKey: [MATERIALS_QUERY_KEY, filters],
    queryFn: () => materialService.getAll(filters),
  })
}
