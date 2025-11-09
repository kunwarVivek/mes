/**
 * useMaterial Hook
 *
 * TanStack Query hook for fetching single material by ID
 */
import { useQuery } from '@tanstack/react-query'
import { materialService } from '../services/material.service'
import { MATERIALS_QUERY_KEY } from './useMaterials'

export function useMaterial(id: number) {
  return useQuery({
    queryKey: [MATERIALS_QUERY_KEY, id],
    queryFn: () => materialService.getById(id),
    enabled: !!id,
  })
}
