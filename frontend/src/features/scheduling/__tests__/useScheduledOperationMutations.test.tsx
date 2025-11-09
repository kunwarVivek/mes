/**
 * Scheduled Operation Mutations Tests
 *
 * TDD: Testing create, update, delete mutation hooks
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCreateScheduledOperation } from '../hooks/useCreateScheduledOperation'
import { useUpdateScheduledOperation } from '../hooks/useUpdateScheduledOperation'
import { useDeleteScheduledOperation } from '../hooks/useDeleteScheduledOperation'
import { schedulingService } from '../services/scheduling.service'
import type { ReactNode } from 'react'
import type {
  CreateScheduledOperationDTO,
  UpdateScheduledOperationDTO,
} from '../types/scheduling.types'

vi.mock('../services/scheduling.service')

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

describe('useCreateScheduledOperation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create scheduled operation successfully', async () => {
    const newOperation: CreateScheduledOperationDTO = {
      organization_id: 1,
      work_order_id: 1,
      operation_sequence: 10,
      operation_name: 'Cutting',
      machine_id: 1,
      scheduled_start: '2024-01-01T08:00:00Z',
      scheduled_end: '2024-01-01T10:00:00Z',
      priority: 5,
    }

    const mockResponse = {
      ...newOperation,
      id: 1,
      status: 'SCHEDULED' as const,
      created_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(schedulingService.create).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useCreateScheduledOperation(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(newOperation)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(schedulingService.create).toHaveBeenCalledWith(newOperation)
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should handle creation errors', async () => {
    const error = new Error('Failed to create scheduled operation')
    vi.mocked(schedulingService.create).mockRejectedValue(error)

    const { result } = renderHook(() => useCreateScheduledOperation(), {
      wrapper: createWrapper(),
    })

    const newOperation: CreateScheduledOperationDTO = {
      organization_id: 1,
      work_order_id: 1,
      operation_sequence: 10,
      operation_name: 'Cutting',
      scheduled_start: '2024-01-01T08:00:00Z',
      scheduled_end: '2024-01-01T10:00:00Z',
      priority: 5,
    }

    result.current.mutate(newOperation)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useUpdateScheduledOperation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update scheduled operation successfully', async () => {
    const updateData: UpdateScheduledOperationDTO = {
      operation_name: 'Updated Cutting',
      priority: 8,
      status: 'IN_PROGRESS',
    }

    const mockResponse = {
      id: 1,
      organization_id: 1,
      work_order_id: 1,
      operation_sequence: 10,
      operation_name: 'Updated Cutting',
      machine_id: 1,
      scheduled_start: '2024-01-01T08:00:00Z',
      scheduled_end: '2024-01-01T10:00:00Z',
      actual_start: '2024-01-01T08:05:00Z',
      status: 'IN_PROGRESS' as const,
      priority: 8,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T08:05:00Z',
    }

    vi.mocked(schedulingService.update).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useUpdateScheduledOperation(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ id: 1, data: updateData })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(schedulingService.update).toHaveBeenCalledWith(1, updateData)
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should handle update errors', async () => {
    const error = new Error('Failed to update scheduled operation')
    vi.mocked(schedulingService.update).mockRejectedValue(error)

    const { result } = renderHook(() => useUpdateScheduledOperation(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ id: 1, data: { operation_name: 'Updated' } })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useDeleteScheduledOperation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should delete scheduled operation successfully', async () => {
    vi.mocked(schedulingService.delete).mockResolvedValue(undefined)

    const { result } = renderHook(() => useDeleteScheduledOperation(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(schedulingService.delete).toHaveBeenCalledWith(1)
  })

  it('should handle deletion errors', async () => {
    const error = new Error('Failed to delete scheduled operation')
    vi.mocked(schedulingService.delete).mockRejectedValue(error)

    const { result } = renderHook(() => useDeleteScheduledOperation(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})
