/**
 * usePMSchedules Hook Tests
 *
 * TDD: Testing TanStack Query hooks with mocked service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { usePMSchedules } from '../hooks/usePMSchedules'
import { maintenanceService } from '../services/maintenance.service'
import type { ReactNode } from 'react'

vi.mock('../services/maintenance.service')

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

describe('usePMSchedules', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch PM schedules successfully', async () => {
    const mockData = [
      {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        schedule_code: 'PM001',
        schedule_name: 'Monthly Lubrication',
        machine_id: 10,
        trigger_type: 'CALENDAR' as const,
        frequency_days: 30,
        meter_threshold: null,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(maintenanceService.getAll).mockResolvedValue(mockData)

    const { result } = renderHook(() => usePMSchedules(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(maintenanceService.getAll).toHaveBeenCalledWith(undefined)
  })

  it('should fetch PM schedules with filters', async () => {
    const mockData = [
      {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        schedule_code: 'PM001',
        schedule_name: 'Monthly Lubrication',
        machine_id: 10,
        trigger_type: 'CALENDAR' as const,
        frequency_days: 30,
        meter_threshold: null,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(maintenanceService.getAll).mockResolvedValue(mockData)

    const filters = {
      machine_id: 10,
      is_active: true,
    }

    const { result } = renderHook(() => usePMSchedules(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
    expect(maintenanceService.getAll).toHaveBeenCalledWith(filters)
  })

  it('should handle errors', async () => {
    const error = new Error('Failed to fetch PM schedules')
    vi.mocked(maintenanceService.getAll).mockRejectedValue(error)

    const { result } = renderHook(() => usePMSchedules(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('should show loading state', () => {
    vi.mocked(maintenanceService.getAll).mockImplementation(
      () => new Promise(() => {})
    )

    const { result } = renderHook(() => usePMSchedules(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })
})
