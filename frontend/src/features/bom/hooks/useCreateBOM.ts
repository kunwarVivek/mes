/**
 * useCreateBOM Hook
 *
 * TanStack Query mutation hook for creating BOMs
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { bomService } from '../services/bom.service'
import { BOMS_QUERY_KEY } from './useBOMs'
import type { CreateBOMDTO } from '../types/bom.types'

export function useCreateBOM() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateBOMDTO) => bomService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [BOMS_QUERY_KEY] })
    },
  })
}
