/**
 * useUpdateBOM Hook
 *
 * TanStack Query mutation hook for updating BOMs
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { bomService } from '../services/bom.service'
import { BOMS_QUERY_KEY } from './useBOMs'
import type { UpdateBOMDTO } from '../types/bom.types'

interface UpdateBOMParams extends UpdateBOMDTO {
  id: number
}

export function useUpdateBOM() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateBOMParams) =>
      bomService.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [BOMS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [BOMS_QUERY_KEY, variables.id] })
    },
  })
}
