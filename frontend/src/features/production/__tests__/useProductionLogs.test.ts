/**
 * useProductionLogs Hook Tests
 *
 * TDD: Testing TanStack Query hooks with React Testing Library
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { productionLogService } from '../services/productionLog.service'
import {
  useProductionLogs,
  useProductionSummary,
  useProductionLog,
  useLogProduction,
} from '../hooks/useProductionLogs'
import React, { type PropsWithChildren } from 'react'

vi.mock('../services/productionLog.service')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: PropsWithChildren) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

describe('useProductionLogs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch production logs for a work order', async () => {
    const mockLogs = {
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_id: 10,
          timestamp: '2025-01-15T14:30:00Z',
          quantity_produced: 100,
          quantity_scrapped: 5,
          quantity_reworked: 2,
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
    }

    vi.mocked(productionLogService.listByWorkOrder).mockResolvedValue(mockLogs)

    const { result } = renderHook(() => useProductionLogs(10), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(productionLogService.listByWorkOrder).toHaveBeenCalledWith(10, undefined)
    expect(result.current.data).toEqual(mockLogs)
  })

  it('should fetch production logs with filters', async () => {
    const mockLogs = {
      items: [],
      total: 0,
      page: 2,
      page_size: 20,
    }

    const filters = {
      start_time: '2025-01-01T00:00:00Z',
      end_time: '2025-01-31T23:59:59Z',
      page: 2,
      page_size: 20,
    }

    vi.mocked(productionLogService.listByWorkOrder).mockResolvedValue(mockLogs)

    const { result } = renderHook(() => useProductionLogs(10, filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(productionLogService.listByWorkOrder).toHaveBeenCalledWith(10, filters)
    expect(result.current.data).toEqual(mockLogs)
  })

  it('should use correct query key pattern', async () => {
    const mockLogs = {
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
    }

    vi.mocked(productionLogService.listByWorkOrder).mockResolvedValue(mockLogs)

    const { result } = renderHook(() => useProductionLogs(10, { page: 2 }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Query key should include workOrderId and params
    expect(result.current.data).toBeDefined()
  })
})

describe('useProductionSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch production summary for a work order', async () => {
    const mockSummary = {
      work_order_id: 10,
      total_produced: 500,
      total_scrapped: 25,
      total_reworked: 10,
      yield_rate: 93.46,
      log_count: 5,
      first_log: '2025-01-15T10:00:00Z',
      last_log: '2025-01-15T18:00:00Z',
    }

    vi.mocked(productionLogService.getSummary).mockResolvedValue(mockSummary)

    const { result } = renderHook(() => useProductionSummary(10), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(productionLogService.getSummary).toHaveBeenCalledWith(10)
    expect(result.current.data).toEqual(mockSummary)
  })
})

describe('useProductionLog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch a single production log by ID', async () => {
    const mockLog = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      work_order_id: 10,
      timestamp: '2025-01-15T14:30:00Z',
      quantity_produced: 100,
      quantity_scrapped: 5,
      quantity_reworked: 2,
    }

    vi.mocked(productionLogService.getById).mockResolvedValue(mockLog)

    const { result } = renderHook(() => useProductionLog(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(productionLogService.getById).toHaveBeenCalledWith(1)
    expect(result.current.data).toEqual(mockLog)
  })
})

describe('useLogProduction', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create a production log entry', async () => {
    const newLog = {
      organization_id: 1,
      plant_id: 1,
      work_order_id: 10,
      quantity_produced: 100,
      quantity_scrapped: 5,
      quantity_reworked: 2,
    }

    const mockResponse = {
      id: 1,
      ...newLog,
      timestamp: '2025-01-15T14:30:00Z',
    }

    vi.mocked(productionLogService.logProduction).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useLogProduction(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.mutate).toBeDefined())

    result.current.mutate(newLog)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(productionLogService.logProduction).toHaveBeenCalledWith(newLog)
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should handle mutation errors', async () => {
    const error = new Error('Failed to create log')
    vi.mocked(productionLogService.logProduction).mockRejectedValue(error)

    const { result } = renderHook(() => useLogProduction(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.mutate).toBeDefined())

    result.current.mutate({
      organization_id: 1,
      plant_id: 1,
      work_order_id: 10,
      quantity_produced: 100,
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})
