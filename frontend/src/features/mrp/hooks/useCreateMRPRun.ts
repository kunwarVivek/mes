/**
 * useCreateMRPRun Hook
 *
 * TanStack Query mutation hook for creating MRP runs
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { mrpService } from '../services/mrp.service'
import { MRP_RUNS_QUERY_KEY } from './useMRPRuns'
import type { CreateMRPRunDTO } from '../types/mrp.types'

export function useCreateMRPRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateMRPRunDTO) => mrpService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [MRP_RUNS_QUERY_KEY] })
    },
  })
}
