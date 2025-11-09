/**
 * usePMSchedule Hook
 *
 * TanStack Query hook for fetching a single PM schedule
 */
import { useQuery } from '@tanstack/react-query'
import { maintenanceService } from '../services/maintenance.service'
import { PM_SCHEDULES_QUERY_KEY } from './usePMSchedules'

export function usePMSchedule(id: number) {
  return useQuery({
    queryKey: [PM_SCHEDULES_QUERY_KEY, id],
    queryFn: () => maintenanceService.getById(id),
    enabled: !!id,
  })
}
