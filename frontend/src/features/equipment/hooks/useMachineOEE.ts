/**
 * useMachineOEE Hook
 *
 * TanStack Query hook for fetching machine OEE metrics
 */
import { useQuery } from '@tanstack/react-query'
import { machineService } from '../services/machine.service'

export const MACHINE_OEE_QUERY_KEY = 'machine-oee'

interface OEEParams {
  machineId: number
  startDate: string
  endDate: string
  idealCycleTime: number
  totalPieces: number
  defectPieces?: number
}

export function useMachineOEE(params: OEEParams) {
  return useQuery({
    queryKey: [MACHINE_OEE_QUERY_KEY, params],
    queryFn: () =>
      machineService.getOEE(params.machineId, {
        start_date: params.startDate,
        end_date: params.endDate,
        ideal_cycle_time: params.idealCycleTime,
        total_pieces: params.totalPieces,
        defect_pieces: params.defectPieces,
      }),
    enabled: !!params.machineId && !!params.startDate && !!params.endDate,
  })
}
