/**
 * Equipment Hooks
 *
 * React Query hooks for equipment/machine operations
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { equipmentService, MachineStatus } from '../services/equipment.service'
import { useAuthStore } from '@/stores/auth.store'

export function useMachines(status?: MachineStatus) {
  const { currentPlant } = useAuthStore()

  return useQuery({
    queryKey: ['machines', currentPlant?.id, status],
    queryFn: () => equipmentService.listMachines({
      plant_id: currentPlant?.id,
      status
    }),
    enabled: !!currentPlant
  })
}

export function useMachine(id: number) {
  return useQuery({
    queryKey: ['machine', id],
    queryFn: () => equipmentService.getMachine(id),
    enabled: !!id
  })
}

export function useOEEMetrics(machineId: number, startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ['oee-metrics', machineId, startDate, endDate],
    queryFn: () => equipmentService.getOEEMetrics(machineId, startDate, endDate),
    enabled: !!machineId,
    refetchInterval: 60000 // Refresh every minute
  })
}

export function useDowntimeHistory(machineId: number, days: number = 7) {
  return useQuery({
    queryKey: ['downtime-history', machineId, days],
    queryFn: () => equipmentService.getDowntimeHistory(machineId, days),
    enabled: !!machineId
  })
}

export function useUpdateMachineStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: MachineStatus }) =>
      equipmentService.updateMachineStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['machines'] })
      queryClient.invalidateQueries({ queryKey: ['machine'] })
    }
  })
}
