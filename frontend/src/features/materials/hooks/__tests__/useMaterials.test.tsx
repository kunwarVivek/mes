import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMaterials } from '../useMaterials'
import { materialService } from '../../services/material.service'
import type { ReactNode } from 'react'

vi.mock('../../services/material.service')

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

  it('fetches materials successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          material_number: 'MAT001',
          material_name: 'Steel Plate',
          organization_id: 1,
          plant_id: 1,
          material_category_id: 1,
          base_uom_id: 1,
          procurement_type: 'PURCHASE',
          mrp_type: 'MRP',
          safety_stock: 0,
          reorder_point: 0,
          lot_size: 1,
          lead_time_days: 0,
          is_active: true,
          created_at: '2025-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 25,
      total_pages: 1,
    }

    vi.mocked(materialService.list).mockResolvedValueOnce(mockData)

    const { result } = renderHook(() => useMaterials(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(materialService.list).toHaveBeenCalledWith(undefined)
  })

  it('passes params to service', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 2,
      page_size: 10,
      total_pages: 0,
    }

    vi.mocked(materialService.list).mockResolvedValueOnce(mockData)

    const params = {
      page: 2,
      page_size: 10,
      search: 'steel',
      procurement_type: 'PURCHASE',
    }

    const { result } = renderHook(() => useMaterials(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(materialService.list).toHaveBeenCalledWith(params)
  })

  it('handles errors', async () => {
    const error = new Error('Network error')
    vi.mocked(materialService.list).mockRejectedValueOnce(error)

    const { result } = renderHook(() => useMaterials(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('uses correct query key', async () => {
    vi.mocked(materialService.list).mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 25,
      total_pages: 0,
    })

    const params = { page: 1, search: 'test' }

    const { result } = renderHook(() => useMaterials(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Query key should include params for proper caching
    expect(materialService.list).toHaveBeenCalledWith(params)
  })
})
