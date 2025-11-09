/**
 * useBOMs Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useBOMs } from '../hooks/useBOMs'
import { bomService } from '../services/bom.service'
import type { ReactNode } from 'react'

vi.mock('../services/bom.service')

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

describe('useBOMs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch BOMs successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          bom_number: 'BOM001',
          material_id: 1,
          bom_version: 1,
          bom_name: 'Test BOM',
          bom_type: 'PRODUCTION' as const,
          base_quantity: 1,
          unit_of_measure_id: 1,
          is_active: true,
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    }

    vi.mocked(bomService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => useBOMs(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(bomService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch BOMs with filters', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }

    vi.mocked(bomService.getAll).mockResolvedValue(mockData)

    const filters = {
      material_id: 1,
      bom_type: 'PRODUCTION' as const,
      page: 1,
      page_size: 20,
    }

    const { result } = renderHook(() => useBOMs(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(bomService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch BOMs')
    vi.mocked(bomService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => useBOMs(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(bomService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useBOMs(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })
})
