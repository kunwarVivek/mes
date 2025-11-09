/**
 * useCreateMaterial Hook
 *
 * TanStack Query mutation hook for creating materials
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { materialService } from '../services/material.service'
import { MATERIALS_QUERY_KEY } from './useMaterials'
import type { CreateMaterialDTO } from '../types/material.types'

export function useCreateMaterial() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateMaterialDTO) => materialService.create(data),
    onSuccess: () => {
      // Invalidate materials list to refetch
      queryClient.invalidateQueries({ queryKey: [MATERIALS_QUERY_KEY] })
    },
  })
}
