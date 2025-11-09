/**
 * useMaterials Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMaterials } from '../hooks/useMaterials'
import { materialService } from '../services/material.service'
import type { ReactNode } from 'react'

vi.mock('../services/material.service')

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

describe('useMaterials', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch materials successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          material_number: 'MAT001',
          material_name: 'Test Material',
          material_category_id: 1,
          base_uom_id: 1,
          procurement_type: 'PURCHASE' as const,
          mrp_type: 'MRP' as const,
          safety_stock: 100,
          reorder_point: 50,
          lot_size: 10,
          lead_time_days: 5,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    }

    vi.mocked(materialService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => useMaterials(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(materialService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch materials with filters', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }

    vi.mocked(materialService.getAll).mockResolvedValue(mockData)

    const filters = {
      category_id: 1,
      procurement_type: 'PURCHASE' as const,
      page: 1,
      page_size: 20,
    }

    const { result } = renderHook(() => useMaterials(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(materialService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch materials')
    vi.mocked(materialService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => useMaterials(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(materialService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useMaterials(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })
})
