/**
 * useDeleteMaterial Hook
 *
 * TanStack Query mutation hook for deleting materials
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { materialService } from '../services/material.service'
import { MATERIALS_QUERY_KEY } from './useMaterials'

export function useDeleteMaterial() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => materialService.delete(id),
    onSuccess: () => {
      // Invalidate materials list to refetch
      queryClient.invalidateQueries({ queryKey: [MATERIALS_QUERY_KEY] })
    },
  })
}
