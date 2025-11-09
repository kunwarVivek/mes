/**
 * useDeleteNCR Hook
 *
 * TanStack Query mutation hook for deleting NCRs
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { qualityService } from '../services/quality.service'
import { NCRS_QUERY_KEY } from './useNCRs'

export function useDeleteNCR() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => qualityService.delete(id),
    onSuccess: () => {
      // Invalidate NCRs list to refetch
      queryClient.invalidateQueries({ queryKey: [NCRS_QUERY_KEY] })
    },
  })
}
