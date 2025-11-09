/**
 * useProductionPlan Hook
 *
 * TanStack Query hook for fetching a single production plan by ID
 */
import { useQuery } from '@tanstack/react-query'
import { productionPlanService } from '../services/productionPlan.service'
import { PRODUCTION_PLANS_QUERY_KEY } from './useProductionPlans'

export function useProductionPlan(id: number) {
  return useQuery({
    queryKey: [PRODUCTION_PLANS_QUERY_KEY, id],
    queryFn: () => productionPlanService.getById(id),
    enabled: !!id,
  })
}
