/**
 * usePMScheduleMutations Hooks
 *
 * TanStack Query mutation hooks for PM schedule CRUD operations
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { maintenanceService } from '../services/maintenance.service'
import { PM_SCHEDULES_QUERY_KEY } from './usePMSchedules'
import type {
  CreatePMScheduleDTO,
  UpdatePMScheduleDTO,
} from '../types/maintenance.types'

export function useCreatePMSchedule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (schedule: CreatePMScheduleDTO) => maintenanceService.create(schedule),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PM_SCHEDULES_QUERY_KEY] })
    },
  })
}

export function useUpdatePMSchedule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdatePMScheduleDTO }) =>
      maintenanceService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PM_SCHEDULES_QUERY_KEY] })
    },
  })
}

export function useDeletePMSchedule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => maintenanceService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PM_SCHEDULES_QUERY_KEY] })
    },
  })
}
