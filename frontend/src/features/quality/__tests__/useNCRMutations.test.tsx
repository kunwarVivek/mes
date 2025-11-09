/**
 * NCR Mutations Hooks Tests
 *
 * TDD: Testing mutation hooks (create, update, delete, review, resolve)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCreateNCR } from '../hooks/useCreateNCR'
import { useUpdateNCR } from '../hooks/useUpdateNCR'
import { useDeleteNCR } from '../hooks/useDeleteNCR'
import { useReviewNCR } from '../hooks/useReviewNCR'
import { useResolveNCR } from '../hooks/useResolveNCR'
import { qualityService } from '../services/quality.service'
import type { ReactNode } from 'react'
import type { CreateNCRDTO, UpdateNCRStatusDTO } from '../types/quality.types'

vi.mock('../services/quality.service')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: {
        retry: false,
      },
      queries: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useCreateNCR', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create NCR successfully', async () => {
    const newNCR: CreateNCRDTO = {
      ncr_number: 'NCR-2024-001',
      work_order_id: 100,
      material_id: 50,
      defect_type: 'DIMENSIONAL',
      defect_description: 'Part dimension out of tolerance by 0.5mm',
      quantity_defective: 5,
      reported_by_user_id: 1,
    }

    const mockResponse = {
      ...newNCR,
      id: 1,
      organization_id: 1,
      plant_id: 1,
      status: 'OPEN' as const,
      created_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(qualityService.create).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useCreateNCR(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(newNCR)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(qualityService.create).toHaveBeenCalledWith(newNCR)
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should handle create errors', async () => {
    const newNCR: CreateNCRDTO = {
      ncr_number: 'NCR-2024-001',
      work_order_id: 100,
      material_id: 50,
      defect_type: 'VISUAL',
      defect_description: 'Surface scratches detected',
      quantity_defective: 3,
      reported_by_user_id: 1,
    }

    const error = new Error('Failed to create NCR')
    vi.mocked(qualityService.create).mockRejectedValue(error)

    const { result } = renderHook(() => useCreateNCR(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(newNCR)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useUpdateNCR', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update NCR status successfully', async () => {
    const statusUpdate: UpdateNCRStatusDTO = {
      status: 'RESOLVED',
      resolution_notes: 'Parts reworked and passed inspection',
      resolved_by_user_id: 2,
    }

    const mockResponse = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      ncr_number: 'NCR-2024-001',
      work_order_id: 100,
      material_id: 50,
      defect_type: 'FUNCTIONAL' as const,
      defect_description: 'Component fails functional test',
      quantity_defective: 10,
      status: 'RESOLVED' as const,
      reported_by_user_id: 1,
      resolution_notes: 'Parts reworked and passed inspection',
      resolved_by_user_id: 2,
      resolved_at: '2024-01-02T00:00:00Z',
      created_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(qualityService.updateStatus).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useUpdateNCR(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ id: 1, data: statusUpdate })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(qualityService.updateStatus).toHaveBeenCalledWith(1, statusUpdate)
    expect(result.current.data).toEqual(mockResponse)
  })
})

describe('useDeleteNCR', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should delete NCR successfully', async () => {
    vi.mocked(qualityService.delete).mockResolvedValue()

    const { result } = renderHook(() => useDeleteNCR(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(qualityService.delete).toHaveBeenCalledWith(1)
  })

  it('should handle delete errors', async () => {
    const error = new Error('Failed to delete NCR')
    vi.mocked(qualityService.delete).mockRejectedValue(error)

    const { result } = renderHook(() => useDeleteNCR(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useReviewNCR', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should review NCR successfully (OPEN → IN_REVIEW)', async () => {
    const mockResponse = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      ncr_number: 'NCR-2024-001',
      work_order_id: 100,
      material_id: 50,
      defect_type: 'MATERIAL' as const,
      defect_description: 'Material contamination detected',
      quantity_defective: 20,
      status: 'IN_REVIEW' as const,
      reported_by_user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(qualityService.review).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useReviewNCR(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(qualityService.review).toHaveBeenCalledWith(1)
    expect(result.current.data).toEqual(mockResponse)
  })
})

describe('useResolveNCR', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should resolve NCR successfully (IN_REVIEW → RESOLVED)', async () => {
    const resolveData = {
      id: 1,
      resolution_notes: 'Root cause identified and corrected',
      resolved_by_user_id: 3,
    }

    const mockResponse = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      ncr_number: 'NCR-2024-001',
      work_order_id: 100,
      material_id: 50,
      defect_type: 'OTHER' as const,
      defect_description: 'Unspecified quality issue',
      quantity_defective: 1,
      status: 'RESOLVED' as const,
      reported_by_user_id: 1,
      resolution_notes: 'Root cause identified and corrected',
      resolved_by_user_id: 3,
      resolved_at: '2024-01-03T00:00:00Z',
      created_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(qualityService.resolve).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useResolveNCR(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(resolveData)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(qualityService.resolve).toHaveBeenCalledWith(
      1,
      'Root cause identified and corrected',
      3
    )
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should handle resolve errors', async () => {
    const resolveData = {
      id: 1,
      resolution_notes: 'Resolution notes',
      resolved_by_user_id: 3,
    }

    const error = new Error('Cannot resolve NCR from current status')
    vi.mocked(qualityService.resolve).mockRejectedValue(error)

    const { result } = renderHook(() => useResolveNCR(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(resolveData)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})
