/**
 * useCreateProductionPlan Hook
 *
 * TanStack Query mutation hook for creating production plans
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { productionPlanService } from '../services/productionPlan.service'
import { PRODUCTION_PLANS_QUERY_KEY } from './useProductionPlans'
import type { CreateProductionPlanDTO } from '../types/productionPlan.types'

export function useCreateProductionPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateProductionPlanDTO) => productionPlanService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PRODUCTION_PLANS_QUERY_KEY] })
    },
  })
}
