/**
 * useDeleteBOM Hook
 *
 * TanStack Query mutation hook for deleting BOMs
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { bomService } from '../services/bom.service'
import { BOMS_QUERY_KEY } from './useBOMs'

export function useDeleteBOM() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => bomService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [BOMS_QUERY_KEY] })
    },
  })
}
