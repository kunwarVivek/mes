/**
 * Production Plan Mutation Hooks Tests
 *
 * TDD: Testing create, update, delete mutation hooks
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCreateProductionPlan } from '../hooks/useCreateProductionPlan'
import { useUpdateProductionPlan } from '../hooks/useUpdateProductionPlan'
import { useDeleteProductionPlan } from '../hooks/useDeleteProductionPlan'
import { productionService } from '../services/production.service'
import type { ReactNode } from 'react'
import type { CreateProductionPlanDTO, UpdateProductionPlanDTO } from '../types/production.types'

vi.mock('../services/production.service')

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

describe('useCreateProductionPlan', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create production plan successfully', async () => {
    const newPlan: CreateProductionPlanDTO = {
      plan_code: 'PLAN001',
      plan_name: 'Q1 Production Plan',
      start_date: '2024-01-01',
      end_date: '2024-03-31',
      status: 'DRAFT',
    }

    const createdPlan = {
      ...newPlan,
      id: 1,
      organization_id: 1,
      created_by_user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(productionService.create).mockResolvedValue(createdPlan)

    const { result } = renderHook(() => useCreateProductionPlan(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(newPlan)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdPlan)
    expect(productionService.create).toHaveBeenCalledWith(newPlan)
  })

  it('should handle creation errors', async () => {
    const error = new Error('Failed to create production plan')
    vi.mocked(productionService.create).mockRejectedValue(error)

    const { result } = renderHook(() => useCreateProductionPlan(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      plan_code: 'PLAN001',
      plan_name: 'Q1 Production Plan',
      start_date: '2024-01-01',
      end_date: '2024-03-31',
      status: 'DRAFT',
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useUpdateProductionPlan', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update production plan successfully', async () => {
    const updateData: UpdateProductionPlanDTO = {
      plan_name: 'Updated Production Plan',
      status: 'APPROVED',
    }

    const updatedPlan = {
      id: 1,
      organization_id: 1,
      plan_code: 'PLAN001',
      plan_name: 'Updated Production Plan',
      start_date: '2024-01-01',
      end_date: '2024-03-31',
      status: 'APPROVED' as const,
      created_by_user_id: 1,
      approved_by_user_id: 1,
      approval_date: '2024-01-02',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    }

    vi.mocked(productionService.update).mockResolvedValue(updatedPlan)

    const { result } = renderHook(() => useUpdateProductionPlan(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ id: 1, data: updateData })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedPlan)
    expect(productionService.update).toHaveBeenCalledWith(1, updateData)
  })
})

describe('useDeleteProductionPlan', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should delete production plan successfully', async () => {
    vi.mocked(productionService.delete).mockResolvedValue(undefined)

    const { result } = renderHook(() => useDeleteProductionPlan(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(productionService.delete).toHaveBeenCalledWith(1)
  })

  it('should handle deletion errors', async () => {
    const error = new Error('Failed to delete production plan')
    vi.mocked(productionService.delete).mockRejectedValue(error)

    const { result } = renderHook(() => useDeleteProductionPlan(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})
