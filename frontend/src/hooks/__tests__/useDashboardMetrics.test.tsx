/**
 * Tests for useDashboardMetrics hook - NEW backend metrics endpoint version
 *
 * Tests the hook that calls /api/v1/metrics/dashboard for aggregated counts
 * (not limited by pagination)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useDashboardMetrics } from '../useDashboardMetrics'
import apiClient from '@/lib/api-client'

// Mock apiClient
vi.mock('@/lib/api-client', () => ({
  default: {
    get: vi.fn(),
  },
}))

describe('useDashboardMetrics (NEW - Backend Metrics Endpoint)', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('should call /api/v1/metrics/dashboard endpoint', async () => {
    const mockMetrics = {
      materials_count: 150,
      work_orders_count: 120,
      ncrs_count: 200,
      work_orders_by_status: {
        PLANNED: 30,
        RELEASED: 40,
        IN_PROGRESS: 25,
        COMPLETED: 20,
        CANCELLED: 5,
      },
      ncrs_by_status: {
        OPEN: 50,
        IN_REVIEW: 75,
        RESOLVED: 60,
        CLOSED: 15,
      },
    }

    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockMetrics })

    const { result } = renderHook(() => useDashboardMetrics(), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    // Verify endpoint called
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/metrics/dashboard')

    // Verify metrics returned
    expect(result.current.metrics).toEqual({
      totalMaterials: 150,
      totalWorkOrders: 120,
      totalNCRs: 200,
      workOrdersByStatus: {
        PLANNED: 30,
        RELEASED: 40,
        IN_PROGRESS: 25,
        COMPLETED: 20,
        CANCELLED: 5,
      },
      ncrsByStatus: {
        OPEN: 50,
        IN_REVIEW: 75,
        RESOLVED: 60,
        CLOSED: 15,
      },
    })
  })

  it('should handle large datasets correctly (>100 items)', async () => {
    const mockMetrics = {
      materials_count: 500,  // Way over 100-item pagination limit
      work_orders_count: 350,
      ncrs_count: 1000,
      work_orders_by_status: {
        PLANNED: 100,
        RELEASED: 100,
        IN_PROGRESS: 75,
        COMPLETED: 50,
        CANCELLED: 25,
      },
      ncrs_by_status: {
        OPEN: 250,
        IN_REVIEW: 350,
        RESOLVED: 300,
        CLOSED: 100,
      },
    }

    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockMetrics })

    const { result } = renderHook(() => useDashboardMetrics(), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    // Verify counts exceed pagination limit
    expect(result.current.metrics?.totalMaterials).toBe(500)
    expect(result.current.metrics?.totalWorkOrders).toBe(350)
    expect(result.current.metrics?.totalNCRs).toBe(1000)
  })

  it('should handle loading state correctly', () => {
    vi.mocked(apiClient.get).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useDashboardMetrics(), { wrapper })

    expect(result.current.isLoading).toBe(true)
    expect(result.current.metrics).toBeUndefined()
  })

  it('should handle error state correctly', async () => {
    const error = new Error('Failed to fetch metrics')
    vi.mocked(apiClient.get).mockRejectedValueOnce(error)

    const { result } = renderHook(() => useDashboardMetrics(), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.error).toBeTruthy()
    expect(result.current.metrics).toBeUndefined()
  })

  it('should transform snake_case API response to camelCase', async () => {
    const mockMetrics = {
      materials_count: 10,
      work_orders_count: 20,
      ncrs_count: 30,
      work_orders_by_status: {
        PLANNED: 5,
        RELEASED: 5,
        IN_PROGRESS: 5,
        COMPLETED: 3,
        CANCELLED: 2,
      },
      ncrs_by_status: {
        OPEN: 10,
        IN_REVIEW: 10,
        RESOLVED: 8,
        CLOSED: 2,
      },
    }

    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockMetrics })

    const { result } = renderHook(() => useDashboardMetrics(), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    // Verify camelCase transformation
    expect(result.current.metrics).toHaveProperty('totalMaterials')
    expect(result.current.metrics).toHaveProperty('totalWorkOrders')
    expect(result.current.metrics).toHaveProperty('totalNCRs')
    expect(result.current.metrics).toHaveProperty('workOrdersByStatus')
    expect(result.current.metrics).toHaveProperty('ncrsByStatus')
  })

  it('should handle empty datasets (zero counts)', async () => {
    const mockMetrics = {
      materials_count: 0,
      work_orders_count: 0,
      ncrs_count: 0,
      work_orders_by_status: {
        PLANNED: 0,
        RELEASED: 0,
        IN_PROGRESS: 0,
        COMPLETED: 0,
        CANCELLED: 0,
      },
      ncrs_by_status: {
        OPEN: 0,
        IN_REVIEW: 0,
        RESOLVED: 0,
        CLOSED: 0,
      },
    }

    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockMetrics })

    const { result } = renderHook(() => useDashboardMetrics(), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.metrics?.totalMaterials).toBe(0)
    expect(result.current.metrics?.totalWorkOrders).toBe(0)
    expect(result.current.metrics?.totalNCRs).toBe(0)
  })
})
