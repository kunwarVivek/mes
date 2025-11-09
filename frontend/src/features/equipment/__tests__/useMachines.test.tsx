/**
 * useMachines Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMachines } from '../hooks/useMachines'
import { machineService } from '../services/machine.service'
import type { ReactNode } from 'react'

vi.mock('../services/machine.service')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useMachines', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch machines successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          machine_code: 'CNC001',
          machine_name: 'CNC Machine 1',
          description: 'High-precision CNC',
          work_center_id: 1,
          status: 'AVAILABLE' as const,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    }

    vi.mocked(machineService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => useMachines(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(machineService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch machines with filters', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }

    vi.mocked(machineService.getAll).mockResolvedValue(mockData)

    const filters = {
      status: 'RUNNING' as const,
      plant_id: 1,
      page: 1,
      page_size: 20,
    }

    const { result } = renderHook(() => useMachines(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(machineService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch machines')
    vi.mocked(machineService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => useMachines(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(machineService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useMachines(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })

  it('should filter by search term', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    }

    vi.mocked(machineService.getAll).mockResolvedValue(mockData)

    const filters = { search: 'CNC' }

    const { result } = renderHook(() => useMachines(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(machineService.getAll).toHaveBeenCalledWith(filters)
  })
})
