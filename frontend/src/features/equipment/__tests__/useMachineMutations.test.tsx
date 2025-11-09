/**
 * Machine Mutation Hooks Tests
 *
 * TDD: Testing TanStack Query mutations for Create, Update, Delete
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useCreateMachine,
  useUpdateMachine,
  useDeleteMachine,
  useUpdateMachineStatus,
} from '../hooks/useMachineMutations'
import { machineService } from '../services/machine.service'
import type { ReactNode } from 'react'
import type { CreateMachineDTO, UpdateMachineDTO, MachineStatusUpdateDTO } from '../types/machine.types'

vi.mock('../services/machine.service')

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

describe('Machine Mutation Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useCreateMachine', () => {
    it('should create a machine successfully', async () => {
      const newMachine: CreateMachineDTO = {
        organization_id: 1,
        plant_id: 1,
        machine_code: 'CNC002',
        machine_name: 'CNC Machine 2',
        description: 'New CNC machine',
        work_center_id: 1,
        status: 'AVAILABLE',
      }

      const mockResponse = {
        id: 2,
        ...newMachine,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(machineService.create).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useCreateMachine(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(newMachine)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockResponse)
      expect(machineService.create).toHaveBeenCalledWith(newMachine)
    })

    it('should handle creation errors', async () => {
      const error = new Error('Machine code already exists')
      vi.mocked(machineService.create).mockRejectedValue(error)

      const { result } = renderHook(() => useCreateMachine(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({} as CreateMachineDTO)

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })

    it('should call onSuccess callback', async () => {
      const onSuccess = vi.fn()
      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        machine_code: 'CNC001',
        machine_name: 'CNC Machine 1',
        description: 'Test',
        work_center_id: 1,
        status: 'AVAILABLE' as const,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(machineService.create).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useCreateMachine({ onSuccess }), {
        wrapper: createWrapper(),
      })

      result.current.mutate({} as CreateMachineDTO)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // TanStack Query v5 only passes data to onSuccess callback, not variables and context
      expect(onSuccess).toHaveBeenCalledWith(mockResponse)
    })
  })

  describe('useUpdateMachine', () => {
    it('should update a machine successfully', async () => {
      const updates: UpdateMachineDTO = {
        machine_name: 'Updated Machine Name',
        description: 'Updated description',
      }

      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        machine_code: 'CNC001',
        machine_name: 'Updated Machine Name',
        description: 'Updated description',
        work_center_id: 1,
        status: 'AVAILABLE' as const,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(machineService.update).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useUpdateMachine(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 1, data: updates })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockResponse)
      expect(machineService.update).toHaveBeenCalledWith(1, updates)
    })

    it('should handle update errors', async () => {
      const error = new Error('Machine not found')
      vi.mocked(machineService.update).mockRejectedValue(error)

      const { result } = renderHook(() => useUpdateMachine(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 999, data: {} })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useDeleteMachine', () => {
    it('should delete a machine successfully', async () => {
      vi.mocked(machineService.delete).mockResolvedValue(undefined)

      const { result } = renderHook(() => useDeleteMachine(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(machineService.delete).toHaveBeenCalledWith(1)
    })

    it('should handle delete errors', async () => {
      const error = new Error('Cannot delete machine in use')
      vi.mocked(machineService.delete).mockRejectedValue(error)

      const { result } = renderHook(() => useDeleteMachine(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })

    it('should call onSuccess callback', async () => {
      const onSuccess = vi.fn()
      vi.mocked(machineService.delete).mockResolvedValue(undefined)

      const { result } = renderHook(() => useDeleteMachine({ onSuccess }), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(onSuccess).toHaveBeenCalled()
    })
  })

  describe('useUpdateMachineStatus', () => {
    it('should update machine status successfully', async () => {
      const statusUpdate: MachineStatusUpdateDTO = {
        status: 'RUNNING',
        notes: 'Production started',
      }

      const mockResponse = {
        machine: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          machine_code: 'CNC001',
          machine_name: 'CNC Machine 1',
          description: 'Test',
          work_center_id: 1,
          status: 'RUNNING' as const,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
        },
        status_history: {
          id: 1,
          machine_id: 1,
          status: 'RUNNING' as const,
          started_at: '2024-01-01T10:00:00Z',
          notes: 'Production started',
        },
      }

      vi.mocked(machineService.updateStatus).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useUpdateMachineStatus(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 1, data: statusUpdate })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockResponse)
      expect(machineService.updateStatus).toHaveBeenCalledWith(1, statusUpdate)
    })

    it('should handle status update errors', async () => {
      const error = new Error('Invalid status transition')
      vi.mocked(machineService.updateStatus).mockRejectedValue(error)

      const { result } = renderHook(() => useUpdateMachineStatus(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 1, data: { status: 'RUNNING' } })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })
})
