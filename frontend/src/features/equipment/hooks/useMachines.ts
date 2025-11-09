/**
 * useMachines Hook
 *
 * TanStack Query hook for fetching machines list
 */
import { useQuery } from '@tanstack/react-query'
import { machineService } from '../services/machine.service'
import type { MachineFilters } from '../types/machine.types'

export const MACHINES_QUERY_KEY = 'machines'

export function useMachines(filters?: MachineFilters) {
  return useQuery({
    queryKey: [MACHINES_QUERY_KEY, filters],
    queryFn: () => machineService.getAll(filters),
  })
}
