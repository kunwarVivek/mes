/**
 * useReviewNCR Hook
 *
 * TanStack Query mutation hook for reviewing NCRs (OPEN → IN_REVIEW)
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { qualityService } from '../services/quality.service'
import { NCRS_QUERY_KEY } from './useNCRs'

export function useReviewNCR() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => qualityService.review(id),
    onSuccess: () => {
      // Invalidate NCRs list to refetch
      queryClient.invalidateQueries({ queryKey: [NCRS_QUERY_KEY] })
    },
  })
}
