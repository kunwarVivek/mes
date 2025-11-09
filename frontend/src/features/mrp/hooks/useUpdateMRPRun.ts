/**
 * useUpdateMRPRun Hook
 *
 * TanStack Query mutation hook for updating MRP runs
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { mrpService } from '../services/mrp.service'
import { MRP_RUNS_QUERY_KEY } from './useMRPRuns'
import type { UpdateMRPRunDTO } from '../types/mrp.types'

export function useUpdateMRPRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateMRPRunDTO }) =>
      mrpService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [MRP_RUNS_QUERY_KEY] })
    },
  })
}
