/**
 * Machine Mutation Hooks
 *
 * TanStack Query mutations for Create, Update, Delete operations
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { machineService } from '../services/machine.service'
import { MACHINES_QUERY_KEY } from './useMachines'
import { MACHINE_QUERY_KEY } from './useMachine'
import type {
  CreateMachineDTO,
  UpdateMachineDTO,
  MachineStatusUpdateDTO,
} from '../types/machine.types'

interface MutationOptions<TData = unknown> {
  onSuccess?: (data: TData) => void
  onError?: (error: Error) => void
}

export function useCreateMachine(options?: MutationOptions) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateMachineDTO) => machineService.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [MACHINES_QUERY_KEY] })
      options?.onSuccess?.(data)
    },
    onError: options?.onError,
  })
}

export function useUpdateMachine(options?: MutationOptions) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateMachineDTO }) =>
      machineService.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [MACHINES_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [MACHINE_QUERY_KEY, data.id] })
      options?.onSuccess?.(data)
    },
    onError: options?.onError,
  })
}

export function useDeleteMachine(options?: MutationOptions) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => machineService.delete(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [MACHINES_QUERY_KEY] })
      options?.onSuccess?.(data)
    },
    onError: options?.onError,
  })
}

export function useUpdateMachineStatus(options?: MutationOptions) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MachineStatusUpdateDTO }) =>
      machineService.updateStatus(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [MACHINES_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [MACHINE_QUERY_KEY, data.machine.id] })
      options?.onSuccess?.(data)
    },
    onError: options?.onError,
  })
}
