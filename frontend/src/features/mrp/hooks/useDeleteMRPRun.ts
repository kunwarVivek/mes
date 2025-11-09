/**
 * useDeleteMRPRun Hook
 *
 * TanStack Query mutation hook for deleting MRP runs
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { mrpService } from '../services/mrp.service'
import { MRP_RUNS_QUERY_KEY } from './useMRPRuns'

export function useDeleteMRPRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => mrpService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [MRP_RUNS_QUERY_KEY] })
    },
  })
}
