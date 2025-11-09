import { useMutation, useQueryClient } from '@tanstack/react-query'
import { materialService } from '../services/material.service'
import { toast } from '@/components/ui/use-toast'
import type { CreateMaterialFormData, UpdateMaterialFormData } from '../schemas/material.schema'

export function useMaterialMutations() {
  const queryClient = useQueryClient()

  const createMaterial = useMutation({
    mutationFn: (data: CreateMaterialFormData) => materialService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      toast({
        title: 'Material created successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to create material',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      })
    },
  })

  const updateMaterial = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateMaterialFormData }) =>
      materialService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      toast({
        title: 'Material updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to update material',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      })
    },
  })

  const deleteMaterial = useMutation({
    mutationFn: (id: number) => materialService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      toast({
        title: 'Material deleted successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to delete material',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      })
    },
  })

  return { createMaterial, updateMaterial, deleteMaterial }
}
