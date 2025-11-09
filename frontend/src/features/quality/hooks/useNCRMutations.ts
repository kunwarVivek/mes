/**
 * NCR Mutation Hooks
 *
 * TanStack Query mutation hooks for NCR operations
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ncrService } from '../services/ncr.service'
import { NCRS_QUERY_KEY, NCR_QUERY_KEY } from './useNCRs'
import type { CreateNCRDTO, UpdateNCRDTO } from '../types/ncr.types'

export function useCreateNCR() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateNCRDTO) => ncrService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NCRS_QUERY_KEY] })
    },
  })
}

export function useUpdateNCR() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateNCRDTO }) =>
      ncrService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NCRS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [NCR_QUERY_KEY] })
    },
  })
}

export function useDeleteNCR() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => ncrService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NCRS_QUERY_KEY] })
    },
  })
}
