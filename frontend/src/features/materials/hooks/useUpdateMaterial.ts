/**
 * useUpdateMaterial Hook
 *
 * TanStack Query mutation hook for updating materials
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { materialService } from '../services/material.service'
import { MATERIALS_QUERY_KEY } from './useMaterials'
import type { UpdateMaterialDTO } from '../types/material.types'

export function useUpdateMaterial() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateMaterialDTO }) =>
      materialService.update(id, data),
    onSuccess: (_, variables) => {
      // Invalidate both list and single material queries
      queryClient.invalidateQueries({ queryKey: [MATERIALS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [MATERIALS_QUERY_KEY, variables.id] })
    },
  })
}
