/**
 * useNCRs Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useNCRs } from '../hooks/useNCRs'
import { qualityService } from '../services/quality.service'
import type { ReactNode } from 'react'

vi.mock('../services/quality.service')

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

describe('useNCRs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch NCRs successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          ncr_number: 'NCR-2024-001',
          work_order_id: 100,
          material_id: 50,
          defect_type: 'DIMENSIONAL' as const,
          defect_description: 'Part dimension out of tolerance',
          quantity_defective: 5,
          status: 'OPEN' as const,
          reported_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    }

    vi.mocked(qualityService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => useNCRs(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(qualityService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch NCRs with filters', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }

    vi.mocked(qualityService.getAll).mockResolvedValue(mockData)

    const filters = {
      status: 'OPEN' as const,
      defect_type: 'DIMENSIONAL' as const,
      page: 1,
      page_size: 20,
    }

    const { result } = renderHook(() => useNCRs(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(qualityService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch NCRs')
    vi.mocked(qualityService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => useNCRs(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(qualityService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useNCRs(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })
})
