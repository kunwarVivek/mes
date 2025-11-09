/**
 * useNCRs Hook
 *
 * TanStack Query hook for fetching NCRs list
 */
import { useQuery } from '@tanstack/react-query'
import { ncrService } from '../services/ncr.service'
import { useAuthStore } from '@/stores/auth.store'
import type { NCRFilters } from '../types/ncr.types'

export const NCRS_QUERY_KEY = 'ncrs'

export function useNCRs(filters?: Omit<NCRFilters, 'plant_id'>) {
  const { currentPlant } = useAuthStore()

  return useQuery({
    queryKey: [NCRS_QUERY_KEY, currentPlant?.id, filters],
    queryFn: () => ncrService.getAll({ plant_id: currentPlant?.id, ...filters }),
    enabled: !!currentPlant,
  })
}
