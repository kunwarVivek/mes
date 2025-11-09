/**
 * useWorkOrder Mutation Hook Tests
 *
 * TDD: Testing mutation hooks (create, update, delete, state transitions)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCreateWorkOrder } from '../hooks/useCreateWorkOrder'
import { useUpdateWorkOrder } from '../hooks/useUpdateWorkOrder'
import { useDeleteWorkOrder } from '../hooks/useDeleteWorkOrder'
import { useReleaseWorkOrder } from '../hooks/useReleaseWorkOrder'
import { useStartWorkOrder } from '../hooks/useStartWorkOrder'
import { useCompleteWorkOrder } from '../hooks/useCompleteWorkOrder'
import { workOrderService } from '../services/workOrder.service'
import type { ReactNode } from 'react'

vi.mock('../services/workOrder.service')

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

describe('Work Order Mutation Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useCreateWorkOrder', () => {
    it('should create work order successfully', async () => {
      const newWorkOrder = {
        material_id: 1,
        order_type: 'PRODUCTION' as const,
        planned_quantity: 100,
        priority: 5,
      }

      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        work_order_number: 'WO001',
        ...newWorkOrder,
        actual_quantity: 0,
        order_status: 'PLANNED' as const,
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(workOrderService.create).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useCreateWorkOrder(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(newWorkOrder)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(workOrderService.create).toHaveBeenCalledWith(newWorkOrder)
      expect(result.current.data).toEqual(mockResponse)
    })

    it('should handle create error', async () => {
      const error = new Error('Failed to create work order')
      vi.mocked(workOrderService.create).mockRejectedValue(error)

      const { result } = renderHook(() => useCreateWorkOrder(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({
        material_id: 1,
        planned_quantity: 100,
      })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useUpdateWorkOrder', () => {
    it('should update work order successfully', async () => {
      const updateData = {
        planned_quantity: 150,
        priority: 8,
      }

      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        work_order_number: 'WO001',
        material_id: 1,
        order_type: 'PRODUCTION' as const,
        order_status: 'PLANNED' as const,
        planned_quantity: 150,
        actual_quantity: 0,
        priority: 8,
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(workOrderService.update).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useUpdateWorkOrder(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 1, ...updateData })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(workOrderService.update).toHaveBeenCalledWith(1, updateData)
      expect(result.current.data).toEqual(mockResponse)
    })
  })

  describe('useDeleteWorkOrder', () => {
    it('should cancel work order successfully', async () => {
      vi.mocked(workOrderService.delete).mockResolvedValue(undefined)

      const { result } = renderHook(() => useDeleteWorkOrder(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(workOrderService.delete).toHaveBeenCalledWith(1)
    })
  })

  describe('useReleaseWorkOrder', () => {
    it('should release work order successfully', async () => {
      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        work_order_number: 'WO001',
        material_id: 1,
        order_type: 'PRODUCTION' as const,
        order_status: 'RELEASED' as const,
        planned_quantity: 100,
        actual_quantity: 0,
        priority: 5,
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(workOrderService.release).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useReleaseWorkOrder(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(workOrderService.release).toHaveBeenCalledWith(1)
      expect(result.current.data?.order_status).toBe('RELEASED')
    })
  })

  describe('useStartWorkOrder', () => {
    it('should start work order successfully', async () => {
      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        work_order_number: 'WO001',
        material_id: 1,
        order_type: 'PRODUCTION' as const,
        order_status: 'IN_PROGRESS' as const,
        planned_quantity: 100,
        actual_quantity: 0,
        priority: 5,
        created_by_user_id: 1,
        start_date_actual: '2024-01-02T00:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(workOrderService.start).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useStartWorkOrder(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(workOrderService.start).toHaveBeenCalledWith(1)
      expect(result.current.data?.order_status).toBe('IN_PROGRESS')
    })
  })

  describe('useCompleteWorkOrder', () => {
    it('should complete work order successfully', async () => {
      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        work_order_number: 'WO001',
        material_id: 1,
        order_type: 'PRODUCTION' as const,
        order_status: 'COMPLETED' as const,
        planned_quantity: 100,
        actual_quantity: 100,
        priority: 5,
        created_by_user_id: 1,
        start_date_actual: '2024-01-02T00:00:00Z',
        end_date_actual: '2024-01-10T00:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-10T00:00:00Z',
      }

      vi.mocked(workOrderService.complete).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useCompleteWorkOrder(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(workOrderService.complete).toHaveBeenCalledWith(1)
      expect(result.current.data?.order_status).toBe('COMPLETED')
    })
  })
})
