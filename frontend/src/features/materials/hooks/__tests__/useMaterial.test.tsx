import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMaterial } from '../useMaterial'
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

describe('useMaterial', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches single material by id', async () => {
    const mockMaterial = {
      id: 1,
      material_number: 'MAT001',
      material_name: 'Steel Plate',
      organization_id: 1,
      plant_id: 1,
      material_category_id: 1,
      base_uom_id: 1,
      procurement_type: 'PURCHASE',
      mrp_type: 'MRP',
      safety_stock: 100,
      reorder_point: 200,
      lot_size: 50,
      lead_time_days: 7,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z',
    }

    vi.mocked(materialService.get).mockResolvedValueOnce(mockMaterial)

    const { result } = renderHook(() => useMaterial(1), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockMaterial)
    expect(materialService.get).toHaveBeenCalledWith(1)
  })

  it('handles errors', async () => {
    const error = new Error('Material not found')
    vi.mocked(materialService.get).mockRejectedValueOnce(error)

    const { result } = renderHook(() => useMaterial(999), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('does not fetch when id is undefined', () => {
    const { result } = renderHook(() => useMaterial(undefined), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(materialService.get).not.toHaveBeenCalled()
  })

  it('uses correct query key with id', async () => {
    vi.mocked(materialService.get).mockResolvedValueOnce({
      id: 5,
      material_number: 'MAT005',
      material_name: 'Test',
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
    })

    const { result } = renderHook(() => useMaterial(5), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(materialService.get).toHaveBeenCalledWith(5)
  })
})
