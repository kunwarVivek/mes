/**
 * useWorkOrders Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWorkOrders } from '../hooks/useWorkOrders'
import { workOrderService } from '../services/workOrder.service'
import type { ReactNode } from 'react'

vi.mock('../services/workOrder.service')

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

describe('useWorkOrders', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch work orders successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_number: 'WO001',
          material_id: 1,
          order_type: 'PRODUCTION' as const,
          order_status: 'PLANNED' as const,
          planned_quantity: 100,
          actual_quantity: 0,
          priority: 5,
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    }

    vi.mocked(workOrderService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => useWorkOrders(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(workOrderService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch work orders with filters', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }

    vi.mocked(workOrderService.getAll).mockResolvedValue(mockData)

    const filters = {
      status: 'PLANNED' as const,
      material_id: 1,
      page: 1,
      page_size: 20,
    }

    const { result } = renderHook(() => useWorkOrders(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(workOrderService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch work orders')
    vi.mocked(workOrderService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => useWorkOrders(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(workOrderService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useWorkOrders(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })
})
