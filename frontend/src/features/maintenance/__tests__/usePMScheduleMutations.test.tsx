/**
 * usePMScheduleMutations Hook Tests
 *
 * TDD: Testing TanStack Query mutation hooks
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useCreatePMSchedule,
  useUpdatePMSchedule,
  useDeletePMSchedule,
} from '../hooks/usePMScheduleMutations'
import { maintenanceService } from '../services/maintenance.service'
import type { ReactNode } from 'react'
import type { CreatePMScheduleDTO, UpdatePMScheduleDTO } from '../types/maintenance.types'

vi.mock('../services/maintenance.service')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('usePMScheduleMutations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useCreatePMSchedule', () => {
    it('should create a PM schedule successfully', async () => {
      const newSchedule: CreatePMScheduleDTO = {
        schedule_code: 'PM002',
        schedule_name: 'Quarterly Inspection',
        machine_id: 10,
        trigger_type: 'CALENDAR',
        frequency_days: 90,
        is_active: true,
      }

      const mockResponse = {
        ...newSchedule,
        id: 2,
        organization_id: 1,
        plant_id: 1,
        meter_threshold: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(maintenanceService.create).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useCreatePMSchedule(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(newSchedule)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(maintenanceService.create).toHaveBeenCalledWith(newSchedule)
      expect(result.current.data).toEqual(mockResponse)
    })

    it('should handle creation errors', async () => {
      const newSchedule: CreatePMScheduleDTO = {
        schedule_code: 'PM002',
        schedule_name: 'Quarterly Inspection',
        machine_id: 10,
        trigger_type: 'CALENDAR',
        frequency_days: 90,
        is_active: true,
      }

      const error = new Error('Failed to create PM schedule')
      vi.mocked(maintenanceService.create).mockRejectedValue(error)

      const { result } = renderHook(() => useCreatePMSchedule(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(newSchedule)

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useUpdatePMSchedule', () => {
    it('should update a PM schedule successfully', async () => {
      const updateData: UpdatePMScheduleDTO = {
        schedule_name: 'Updated Schedule',
        frequency_days: 45,
      }

      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        schedule_code: 'PM001',
        schedule_name: 'Updated Schedule',
        machine_id: 10,
        trigger_type: 'CALENDAR' as const,
        frequency_days: 45,
        meter_threshold: null,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(maintenanceService.update).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useUpdatePMSchedule(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 1, data: updateData })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(maintenanceService.update).toHaveBeenCalledWith(1, updateData)
      expect(result.current.data).toEqual(mockResponse)
    })

    it('should handle update errors', async () => {
      const updateData: UpdatePMScheduleDTO = {
        schedule_name: 'Updated Schedule',
      }

      const error = new Error('Failed to update PM schedule')
      vi.mocked(maintenanceService.update).mockRejectedValue(error)

      const { result } = renderHook(() => useUpdatePMSchedule(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 1, data: updateData })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useDeletePMSchedule', () => {
    it('should delete a PM schedule successfully', async () => {
      vi.mocked(maintenanceService.delete).mockResolvedValue()

      const { result } = renderHook(() => useDeletePMSchedule(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(maintenanceService.delete).toHaveBeenCalledWith(1)
    })

    it('should handle deletion errors', async () => {
      const error = new Error('Failed to delete PM schedule')
      vi.mocked(maintenanceService.delete).mockRejectedValue(error)

      const { result } = renderHook(() => useDeletePMSchedule(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })
})
