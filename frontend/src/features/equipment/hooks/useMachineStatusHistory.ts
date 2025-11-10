/**
 * useMachineStatusHistory Hook
 *
 * TanStack Query hook for fetching machine status history
 */
import { useQuery } from '@tanstack/react-query'
import { machineService } from '../services/machine.service'

export const MACHINE_STATUS_HISTORY_QUERY_KEY = 'machine-status-history'

interface StatusHistoryParams {
  machineId: number
  startDate?: string
  endDate?: string
  limit?: number
}

export function useMachineStatusHistory(params: StatusHistoryParams) {
  return useQuery({
    queryKey: [MACHINE_STATUS_HISTORY_QUERY_KEY, params],
    queryFn: () =>
      machineService.getStatusHistory(params.machineId, {
        start_date: params.startDate,
        end_date: params.endDate,
        limit: params.limit,
      }),
    enabled: !!params.machineId,
  })
}
