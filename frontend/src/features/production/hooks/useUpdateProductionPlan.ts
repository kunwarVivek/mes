/**
 * useUpdateProductionPlan Hook
 *
 * TanStack Query mutation hook for updating production plans
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { productionService } from '../services/production.service'
import { PRODUCTION_PLANS_QUERY_KEY } from './useProductionPlans'
import type { UpdateProductionPlanDTO } from '../types/production.types'

export function useUpdateProductionPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateProductionPlanDTO }) =>
      productionService.update(id, data),
    onSuccess: () => {
      // Invalidate production plans to refetch
      queryClient.invalidateQueries({ queryKey: [PRODUCTION_PLANS_QUERY_KEY] })
    },
  })
}
