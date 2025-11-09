/**
 * useMaterials Hook
 *
 * TanStack Query hook for fetching materials list
 */
import { useQuery } from '@tanstack/react-query'
import { materialService, type MaterialListParams } from '../services/material.service'

export function useMaterials(params?: MaterialListParams) {
  return useQuery({
    queryKey: ['materials', params],
    queryFn: () => materialService.list(params),
  })
}
