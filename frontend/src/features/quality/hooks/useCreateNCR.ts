/**
 * useCreateNCR Hook
 *
 * TanStack Query mutation hook for creating NCRs
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { qualityService } from '../services/quality.service'
import { NCRS_QUERY_KEY } from './useNCRs'
import type { CreateNCRDTO } from '../types/quality.types'

export function useCreateNCR() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateNCRDTO) => qualityService.create(data),
    onSuccess: () => {
      // Invalidate NCRs list to refetch
      queryClient.invalidateQueries({ queryKey: [NCRS_QUERY_KEY] })
    },
  })
}
