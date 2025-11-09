/**
 * useMRPRuns Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMRPRuns } from '../hooks/useMRPRuns'
import { mrpService } from '../services/mrp.service'
import type { ReactNode } from 'react'

vi.mock('../services/mrp.service')

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

describe('useMRPRuns', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch MRP runs successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          organization_id: 1,
          run_code: 'MRP001',
          run_name: 'Test MRP Run',
          run_date: '2024-01-01',
          planning_horizon_days: 30,
          status: 'DRAFT' as const,
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    }

    vi.mocked(mrpService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => useMRPRuns(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(mrpService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch MRP runs with filters', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }

    vi.mocked(mrpService.getAll).mockResolvedValue(mockData)

    const filters = {
      status: 'COMPLETED' as const,
      page: 1,
      page_size: 20,
    }

    const { result } = renderHook(() => useMRPRuns(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(mrpService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch MRP runs')
    vi.mocked(mrpService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => useMRPRuns(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(mrpService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useMRPRuns(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })
})
