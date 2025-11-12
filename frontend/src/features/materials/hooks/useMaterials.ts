/**
 * useMaterials Hook
 *
 * TanStack Query hook for fetching materials list
 */
import { useQuery } from '@tanstack/react-query'
import { materialService, type MaterialListParams } from '../services/material.service'

export const MATERIALS_QUERY_KEY = 'materials'

export function useMaterials(params?: MaterialListParams) {
  return useQuery({
    queryKey: [MATERIALS_QUERY_KEY, params],
    queryFn: () => materialService.list(params),
  })
}
