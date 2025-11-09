/**
 * useShift Hook
 *
 * TanStack Query hook for fetching a single shift by ID
 */
import { useQuery } from '@tanstack/react-query'
import { shiftService } from '../services/shift.service'
import { SHIFTS_QUERY_KEY } from './useShifts'

export function useShift(id: number) {
  return useQuery({
    queryKey: [SHIFTS_QUERY_KEY, id],
    queryFn: () => shiftService.getById(id),
    enabled: !!id,
  })
}
