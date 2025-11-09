/**
 * useNCRMutations Hook
 *
 * TanStack Query mutations for NCR operations
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useToast } from '@/components/ui/use-toast'
import { ncrService } from '../services/ncr.service'
import type { CreateNCRFormData, UpdateNCRStatusFormData } from '../schemas/ncr.schema'

export function useNCRMutations() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const createNCR = useMutation({
    mutationFn: (data: CreateNCRFormData) => ncrService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ncrs'] })
      toast({
        title: 'Success',
        description: 'NCR created successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create NCR',
        variant: 'destructive',
      })
    },
  })

  const updateNCRStatus = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateNCRStatusFormData }) =>
      ncrService.updateStatus(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ncrs'] })
      toast({
        title: 'Success',
        description: 'NCR status updated successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update NCR status',
        variant: 'destructive',
      })
    },
  })

  return {
    createNCR,
    updateNCRStatus,
  }
}
