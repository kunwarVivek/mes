/**
 * useShiftMutations Hook Tests
 *
 * TDD: Testing mutation hooks (create, update, delete)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCreateShift, useUpdateShift, useCreateHandover } from '../hooks/useShiftMutations'
import { shiftService } from '../services/shift.service'
import type { ReactNode } from 'react'
import type { CreateShiftDTO, UpdateShiftDTO, CreateShiftHandoverDTO } from '../types/shift.types'

vi.mock('../services/shift.service')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useCreateShift', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create a shift successfully', async () => {
    const newShift: CreateShiftDTO = {
      shift_name: 'Night Shift',
      shift_code: 'C',
      start_time: '22:00:00',
      end_time: '06:00:00',
      production_target: 800,
      is_active: true,
    }

    const mockResponse = {
      ...newShift,
      id: 2,
      organization_id: 1,
      plant_id: 1,
      created_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(shiftService.create).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useCreateShift(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(newShift)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockResponse)
    expect(shiftService.create).toHaveBeenCalledWith(newShift)
  })

  it('should handle create errors', async () => {
    const newShift: CreateShiftDTO = {
      shift_name: 'Night Shift',
      shift_code: 'C',
      start_time: '22:00:00',
      end_time: '06:00:00',
      production_target: 800,
      is_active: true,
    }

    const error = new Error('Shift code already exists')
    vi.mocked(shiftService.create).mockRejectedValue(error)

    const { result } = renderHook(() => useCreateShift(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(newShift)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useUpdateShift', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update a shift successfully', async () => {
    const updateData: UpdateShiftDTO = {
      shift_name: 'Updated Morning Shift',
      production_target: 1200,
    }

    const mockResponse = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      shift_code: 'A',
      shift_name: 'Updated Morning Shift',
      start_time: '06:00:00',
      end_time: '14:00:00',
      production_target: 1200,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    }

    vi.mocked(shiftService.update).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useUpdateShift(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ id: 1, data: updateData })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockResponse)
    expect(shiftService.update).toHaveBeenCalledWith(1, updateData)
  })

  it('should handle update errors', async () => {
    const updateData: UpdateShiftDTO = {
      shift_name: 'Updated Morning Shift',
    }

    const error = new Error('Shift not found')
    vi.mocked(shiftService.update).mockRejectedValue(error)

    const { result } = renderHook(() => useUpdateShift(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ id: 999, data: updateData })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useCreateHandover', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create a handover successfully', async () => {
    const handoverData: CreateShiftHandoverDTO = {
      from_shift_id: 1,
      to_shift_id: 2,
      handover_date: '2024-01-01T14:00:00Z',
      wip_quantity: 50,
      production_summary: 'Completed 950 units, 50 in progress',
      quality_issues: 'None',
    }

    const mockResponse = {
      ...handoverData,
      id: 1,
      organization_id: 1,
      plant_id: 1,
      handover_by_user_id: 1,
      created_at: '2024-01-01T14:00:00Z',
    }

    vi.mocked(shiftService.createHandover).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useCreateHandover(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(handoverData)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockResponse)
    expect(shiftService.createHandover).toHaveBeenCalledWith(handoverData)
  })

  it('should handle handover creation errors', async () => {
    const handoverData: CreateShiftHandoverDTO = {
      from_shift_id: 1,
      to_shift_id: 1, // Same shift - should fail
      handover_date: '2024-01-01T14:00:00Z',
      wip_quantity: 50,
      production_summary: 'Test',
    }

    const error = new Error('Cannot handover to the same shift')
    vi.mocked(shiftService.createHandover).mockRejectedValue(error)

    const { result } = renderHook(() => useCreateHandover(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(handoverData)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})
