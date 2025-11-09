/**
 * useScheduledOperations Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useScheduledOperations } from '../hooks/useScheduledOperations'
import { schedulingService } from '../services/scheduling.service'
import type { ReactNode } from 'react'

vi.mock('../services/scheduling.service')

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

describe('useScheduledOperations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch scheduled operations successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          organization_id: 1,
          work_order_id: 1,
          operation_sequence: 10,
          operation_name: 'Cutting',
          machine_id: 1,
          scheduled_start: '2024-01-01T08:00:00Z',
          scheduled_end: '2024-01-01T10:00:00Z',
          status: 'SCHEDULED' as const,
          priority: 5,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    }

    vi.mocked(schedulingService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => useScheduledOperations(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(schedulingService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch scheduled operations with filters', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }

    vi.mocked(schedulingService.getAll).mockResolvedValue(mockData)

    const filters = {
      work_order_id: 1,
      status: 'COMPLETED' as const,
      page: 1,
      page_size: 20,
    }

    const { result } = renderHook(() => useScheduledOperations(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(schedulingService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch scheduled operations')
    vi.mocked(schedulingService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => useScheduledOperations(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(schedulingService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useScheduledOperations(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })
})
