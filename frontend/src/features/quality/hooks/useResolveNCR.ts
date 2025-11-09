/**
 * useResolveNCR Hook
 *
 * TanStack Query mutation hook for resolving NCRs (IN_REVIEW → RESOLVED)
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { qualityService } from '../services/quality.service'
import { NCRS_QUERY_KEY } from './useNCRs'

export function useResolveNCR() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, resolution_notes, resolved_by_user_id }: {
      id: number
      resolution_notes: string
      resolved_by_user_id: number
    }) => qualityService.resolve(id, resolution_notes, resolved_by_user_id),
    onSuccess: () => {
      // Invalidate NCRs list to refetch
      queryClient.invalidateQueries({ queryKey: [NCRS_QUERY_KEY] })
    },
  })
}
