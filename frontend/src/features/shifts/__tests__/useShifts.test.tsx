/**
 * useShifts Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useShifts } from '../hooks/useShifts'
import { shiftService } from '../services/shift.service'
import type { ReactNode } from 'react'

vi.mock('../services/shift.service')

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

describe('useShifts', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch shifts successfully', async () => {
    const mockData = {
      items: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          shift_code: 'A',
          shift_name: 'Morning Shift',
          start_time: '06:00:00',
          end_time: '14:00:00',
          production_target: 1000,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    }

    vi.mocked(shiftService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => useShifts(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(shiftService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch shifts with filters', async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }

    vi.mocked(shiftService.getAll).mockResolvedValue(mockData)

    const filters = {
      is_active: true,
      shift_code: 'A',
      page: 1,
      page_size: 20,
    }

    const { result } = renderHook(() => useShifts(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(shiftService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch shifts')
    vi.mocked(shiftService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => useShifts(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(shiftService.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(() => useShifts(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })
})
