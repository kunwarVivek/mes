/**
 * useMaterial Hook
 *
 * TanStack Query hook for fetching single material by ID
 */
import { useQuery } from '@tanstack/react-query'
import { materialService } from '../services/material.service'

export function useMaterial(id: number | undefined) {
  return useQuery({
    queryKey: ['materials', id],
    queryFn: () => materialService.get(id!),
    enabled: !!id,
  })
}
