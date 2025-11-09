/**
 * MRP Run Mutations Tests
 *
 * TDD: Testing create, update, delete mutation hooks
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCreateMRPRun } from '../hooks/useCreateMRPRun'
import { useUpdateMRPRun } from '../hooks/useUpdateMRPRun'
import { useDeleteMRPRun } from '../hooks/useDeleteMRPRun'
import { mrpService } from '../services/mrp.service'
import type { ReactNode } from 'react'
import type { CreateMRPRunDTO, UpdateMRPRunDTO } from '../types/mrp.types'

vi.mock('../services/mrp.service')

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

describe('useCreateMRPRun', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create MRP run successfully', async () => {
    const newMRPRun: CreateMRPRunDTO = {
      organization_id: 1,
      run_code: 'MRP001',
      run_name: 'Test MRP Run',
      run_date: '2024-01-01',
      planning_horizon_days: 30,
      created_by_user_id: 1,
    }

    const mockResponse = {
      ...newMRPRun,
      id: 1,
      status: 'DRAFT' as const,
      created_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(mrpService.create).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useCreateMRPRun(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(newMRPRun)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mrpService.create).toHaveBeenCalledWith(newMRPRun)
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should handle creation errors', async () => {
    const error = new Error('Failed to create MRP run')
    vi.mocked(mrpService.create).mockRejectedValue(error)

    const { result } = renderHook(() => useCreateMRPRun(), {
      wrapper: createWrapper(),
    })

    const newMRPRun: CreateMRPRunDTO = {
      organization_id: 1,
      run_code: 'MRP001',
      run_name: 'Test MRP Run',
      run_date: '2024-01-01',
      planning_horizon_days: 30,
      created_by_user_id: 1,
    }

    result.current.mutate(newMRPRun)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useUpdateMRPRun', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update MRP run successfully', async () => {
    const updateData: UpdateMRPRunDTO = {
      run_name: 'Updated MRP Run',
      planning_horizon_days: 60,
    }

    const mockResponse = {
      id: 1,
      organization_id: 1,
      run_code: 'MRP001',
      run_name: 'Updated MRP Run',
      run_date: '2024-01-01',
      planning_horizon_days: 60,
      status: 'DRAFT' as const,
      created_by_user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    }

    vi.mocked(mrpService.update).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useUpdateMRPRun(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ id: 1, data: updateData })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mrpService.update).toHaveBeenCalledWith(1, updateData)
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should handle update errors', async () => {
    const error = new Error('Failed to update MRP run')
    vi.mocked(mrpService.update).mockRejectedValue(error)

    const { result } = renderHook(() => useUpdateMRPRun(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ id: 1, data: { run_name: 'Updated' } })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useDeleteMRPRun', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should delete MRP run successfully', async () => {
    vi.mocked(mrpService.delete).mockResolvedValue(undefined)

    const { result } = renderHook(() => useDeleteMRPRun(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mrpService.delete).toHaveBeenCalledWith(1)
  })

  it('should handle deletion errors', async () => {
    const error = new Error('Failed to delete MRP run')
    vi.mocked(mrpService.delete).mockRejectedValue(error)

    const { result } = renderHook(() => useDeleteMRPRun(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})
