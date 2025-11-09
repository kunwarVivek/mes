/**
 * useShifts Hook
 *
 * TanStack Query hook for fetching shifts list
 */
import { useQuery } from '@tanstack/react-query'
import { shiftService } from '../services/shift.service'
import type { ShiftFilters } from '../types/shift.types'

export const SHIFTS_QUERY_KEY = 'shifts'

export function useShifts(filters?: ShiftFilters) {
  return useQuery({
    queryKey: [SHIFTS_QUERY_KEY, filters],
    queryFn: () => shiftService.getAll(filters),
  })
}
