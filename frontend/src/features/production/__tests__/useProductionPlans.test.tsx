/**
 * useProductionPlans Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useProductionPlans } from '../hooks/useProductionPlans'
import { productionService } from '../services/production.service'
import type { ReactNode } from 'react'

vi.mock('../services/production.service')

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

describe('useProductionPlans', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch production plans successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          organization_id: 1,
          plan_code: 'PLAN001',
          plan_name: 'Q1 Production Plan',
          start_date: '2024-01-01',
          end_date: '2024-03-31',
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

    vi.mocked(productionService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => useProductionPlans(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(productionService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch production plans with filters', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }

    vi.mocked(productionService.getAll).mockResolvedValue(mockData)

    const filters = {
      status: 'APPROVED' as const,
      start_date_from: '2024-01-01',
      page: 1,
      page_size: 20,
    }

    const { result } = renderHook(() => useProductionPlans(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(productionService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch production plans')
    vi.mocked(productionService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => useProductionPlans(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(productionService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useProductionPlans(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })
})
