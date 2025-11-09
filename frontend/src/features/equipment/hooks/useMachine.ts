/**
 * useMachine Hook
 *
 * TanStack Query hook for fetching a single machine
 */
import { useQuery } from '@tanstack/react-query'
import { machineService } from '../services/machine.service'

export const MACHINE_QUERY_KEY = 'machine'

export function useMachine(id: number) {
  return useQuery({
    queryKey: [MACHINE_QUERY_KEY, id],
    queryFn: () => machineService.getById(id),
    enabled: !!id,
  })
}
