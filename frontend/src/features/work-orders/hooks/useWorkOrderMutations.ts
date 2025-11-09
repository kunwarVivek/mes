import { useMutation, useQueryClient } from '@tanstack/react-query'
import { workOrderService } from '../services/work-order.service'
import { toast } from '@/components/ui/use-toast'
import type { CreateWorkOrderFormData, UpdateWorkOrderFormData } from '../schemas/work-order.schema'

export function useWorkOrderMutations() {
  const queryClient = useQueryClient()

  const createWorkOrder = useMutation({
    mutationFn: (data: CreateWorkOrderFormData) => workOrderService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-orders'] })
      toast({
        title: 'Work order created successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to create work order',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      })
    },
  })

  const updateWorkOrder = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateWorkOrderFormData }) =>
      workOrderService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-orders'] })
      toast({
        title: 'Work order updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to update work order',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      })
    },
  })

  const cancelWorkOrder = useMutation({
    mutationFn: (id: number) => workOrderService.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-orders'] })
      toast({
        title: 'Work order cancelled successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to cancel work order',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      })
    },
  })

  const releaseWorkOrder = useMutation({
    mutationFn: (id: number) => workOrderService.release(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-orders'] })
      toast({
        title: 'Work order released successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to release work order',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      })
    },
  })

  const startWorkOrder = useMutation({
    mutationFn: (id: number) => workOrderService.start(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-orders'] })
      toast({
        title: 'Work order started successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to start work order',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      })
    },
  })

  const completeWorkOrder = useMutation({
    mutationFn: (id: number) => workOrderService.complete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-orders'] })
      toast({
        title: 'Work order completed successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to complete work order',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      })
    },
  })

  return {
    createWorkOrder,
    updateWorkOrder,
    cancelWorkOrder,
    releaseWorkOrder,
    startWorkOrder,
    completeWorkOrder,
  }
}
