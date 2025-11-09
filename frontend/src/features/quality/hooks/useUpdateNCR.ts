/**
 * useUpdateNCR Hook
 *
 * TanStack Query mutation hook for updating NCR status
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { qualityService } from '../services/quality.service'
import { NCRS_QUERY_KEY } from './useNCRs'
import type { UpdateNCRStatusDTO } from '../types/quality.types'

export function useUpdateNCR() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateNCRStatusDTO }) =>
      qualityService.updateStatus(id, data),
    onSuccess: () => {
      // Invalidate NCRs list to refetch
      queryClient.invalidateQueries({ queryKey: [NCRS_QUERY_KEY] })
    },
  })
}
