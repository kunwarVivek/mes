/**
 * useUpdateProductionPlan Hook
 *
 * TanStack Query mutation hook for updating production plans
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { productionPlanService } from '../services/productionPlan.service'
import { PRODUCTION_PLANS_QUERY_KEY } from './useProductionPlans'
import type { UpdateProductionPlanDTO } from '../types/productionPlan.types'

interface UpdateProductionPlanParams extends UpdateProductionPlanDTO {
  id: number
}

export function useUpdateProductionPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateProductionPlanParams) =>
      productionPlanService.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [PRODUCTION_PLANS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [PRODUCTION_PLANS_QUERY_KEY, variables.id] })
    },
  })
}
