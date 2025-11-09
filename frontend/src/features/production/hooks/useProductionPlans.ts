/**
 * useProductionPlans Hook
 *
 * TanStack Query hook for fetching production plans list
 */
import { useQuery } from '@tanstack/react-query'
import { productionService } from '../services/production.service'
import type { ProductionPlanFilters } from '../types/production.types'

export const PRODUCTION_PLANS_QUERY_KEY = 'production-plans'

export function useProductionPlans(filters?: ProductionPlanFilters) {
  return useQuery({
    queryKey: [PRODUCTION_PLANS_QUERY_KEY, filters],
    queryFn: () => productionService.getAll(filters),
  })
}
