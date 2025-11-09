/**
 * useShiftMutations Hooks
 *
 * TanStack Query mutation hooks for shift CRUD operations
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { shiftService } from '../services/shift.service'
import { SHIFTS_QUERY_KEY } from './useShifts'
import type { CreateShiftDTO, UpdateShiftDTO, CreateShiftHandoverDTO } from '../types/shift.types'

/**
 * Create shift mutation hook
 */
export function useCreateShift() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateShiftDTO) => shiftService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [SHIFTS_QUERY_KEY] })
    },
  })
}

/**
 * Update shift mutation hook
 */
export function useUpdateShift() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateShiftDTO }) =>
      shiftService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [SHIFTS_QUERY_KEY] })
    },
  })
}

/**
 * Create shift handover mutation hook
 */
export function useCreateHandover() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateShiftHandoverDTO) => shiftService.createHandover(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shift-handovers'] })
    },
  })
}
