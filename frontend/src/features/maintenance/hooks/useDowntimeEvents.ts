/**
 * useDowntimeEvents Hook
 *
 * TanStack Query hook for fetching downtime events
 */
import { useQuery } from '@tanstack/react-query'
import { maintenanceService } from '../services/maintenance.service'
import type { DowntimeEventFilters } from '../types/maintenance.types'

export const DOWNTIME_EVENTS_QUERY_KEY = 'downtime-events'

export function useDowntimeEvents(filters?: DowntimeEventFilters) {
  return useQuery({
    queryKey: [DOWNTIME_EVENTS_QUERY_KEY, filters],
    queryFn: () => maintenanceService.getDowntimeEvents(filters),
  })
}
