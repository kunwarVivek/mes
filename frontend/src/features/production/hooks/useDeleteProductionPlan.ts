/**
 * useDeleteProductionPlan Hook
 *
 * TanStack Query mutation hook for deleting production plans
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { productionService } from '../services/production.service'
import { PRODUCTION_PLANS_QUERY_KEY } from './useProductionPlans'

export function useDeleteProductionPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => productionService.delete(id),
    onSuccess: () => {
      // Invalidate production plans to refetch
      queryClient.invalidateQueries({ queryKey: [PRODUCTION_PLANS_QUERY_KEY] })
    },
  })
}
