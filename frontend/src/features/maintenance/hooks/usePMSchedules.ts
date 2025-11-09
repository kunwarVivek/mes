/**
 * usePMSchedules Hook
 *
 * TanStack Query hook for fetching PM schedules list
 */
import { useQuery } from '@tanstack/react-query'
import { maintenanceService } from '../services/maintenance.service'
import type { PMScheduleFilters } from '../types/maintenance.types'

export const PM_SCHEDULES_QUERY_KEY = 'pm-schedules'

export function usePMSchedules(filters?: PMScheduleFilters) {
  return useQuery({
    queryKey: [PM_SCHEDULES_QUERY_KEY, filters],
    queryFn: () => maintenanceService.getAll(filters),
  })
}
