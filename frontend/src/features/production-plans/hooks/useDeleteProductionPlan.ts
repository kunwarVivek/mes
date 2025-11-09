/**
 * useDeleteProductionPlan Hook
 *
 * TanStack Query mutation hook for deleting production plans
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { productionPlanService } from '../services/productionPlan.service'
import { PRODUCTION_PLANS_QUERY_KEY } from './useProductionPlans'

export function useDeleteProductionPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => productionPlanService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PRODUCTION_PLANS_QUERY_KEY] })
    },
  })
}
