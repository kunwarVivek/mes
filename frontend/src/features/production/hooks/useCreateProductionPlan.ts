/**
 * useCreateProductionPlan Hook
 *
 * TanStack Query mutation hook for creating production plans
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { productionService } from '../services/production.service'
import { PRODUCTION_PLANS_QUERY_KEY } from './useProductionPlans'
import type { CreateProductionPlanDTO } from '../types/production.types'

export function useCreateProductionPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateProductionPlanDTO) => productionService.create(data),
    onSuccess: () => {
      // Invalidate production plans list to refetch
      queryClient.invalidateQueries({ queryKey: [PRODUCTION_PLANS_QUERY_KEY] })
    },
  })
}
