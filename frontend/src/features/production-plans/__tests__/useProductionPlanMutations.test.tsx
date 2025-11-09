/**
 * useProductionPlan Mutation Hook Tests
 *
 * TDD: Testing mutation hooks (create, update, delete)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCreateProductionPlan } from '../hooks/useCreateProductionPlan'
import { useUpdateProductionPlan } from '../hooks/useUpdateProductionPlan'
import { useDeleteProductionPlan } from '../hooks/useDeleteProductionPlan'
import { productionPlanService } from '../services/productionPlan.service'
import type { ReactNode } from 'react'

vi.mock('../services/productionPlan.service')

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

describe('Production Plan Mutation Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useCreateProductionPlan', () => {
    it('should create production plan successfully', async () => {
      const newPlan = {
        plan_code: 'PLAN002',
        plan_name: 'Q2 2024 Plan',
        start_date: '2024-04-01',
        end_date: '2024-06-30',
        status: 'DRAFT' as const,
      }

      const mockResponse = {
        id: 2,
        organization_id: 1,
        plant_id: 1,
        ...newPlan,
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(productionPlanService.create).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useCreateProductionPlan(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(newPlan)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(productionPlanService.create).toHaveBeenCalledWith(newPlan)
      expect(result.current.data).toEqual(mockResponse)
    })

    it('should handle create error', async () => {
      const error = new Error('Failed to create production plan')
      vi.mocked(productionPlanService.create).mockRejectedValue(error)

      const { result } = renderHook(() => useCreateProductionPlan(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({
        plan_code: 'PLAN002',
        plan_name: 'Q2 2024 Plan',
        start_date: '2024-04-01',
        end_date: '2024-06-30',
      })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useUpdateProductionPlan', () => {
    it('should update production plan successfully', async () => {
      const updateData = {
        plan_name: 'Updated Q1 2024 Plan',
        status: 'APPROVED' as const,
      }

      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        plan_code: 'PLAN001',
        plan_name: 'Updated Q1 2024 Plan',
        start_date: '2024-01-01',
        end_date: '2024-03-31',
        status: 'APPROVED' as const,
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(productionPlanService.update).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useUpdateProductionPlan(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 1, ...updateData })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(productionPlanService.update).toHaveBeenCalledWith(1, updateData)
      expect(result.current.data).toEqual(mockResponse)
    })
  })

  describe('useDeleteProductionPlan', () => {
    it('should delete production plan successfully', async () => {
      vi.mocked(productionPlanService.delete).mockResolvedValue(undefined)

      const { result } = renderHook(() => useDeleteProductionPlan(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(productionPlanService.delete).toHaveBeenCalledWith(1)
    })
  })
})
