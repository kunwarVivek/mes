/**
 * useBOM Mutation Hook Tests
 *
 * TDD: Testing mutation hooks (create, update, delete)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCreateBOM } from '../hooks/useCreateBOM'
import { useUpdateBOM } from '../hooks/useUpdateBOM'
import { useDeleteBOM } from '../hooks/useDeleteBOM'
import { bomService } from '../services/bom.service'
import type { ReactNode } from 'react'

vi.mock('../services/bom.service')

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

describe('BOM Mutation Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useCreateBOM', () => {
    it('should create BOM successfully', async () => {
      const newBOM = {
        bom_number: 'BOM002',
        material_id: 1,
        bom_name: 'New BOM',
        bom_type: 'PRODUCTION' as const,
        base_quantity: 1,
        unit_of_measure_id: 1,
      }

      const mockResponse = {
        id: 2,
        organization_id: 1,
        plant_id: 1,
        ...newBOM,
        bom_version: 1,
        is_active: true,
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(bomService.create).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useCreateBOM(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(newBOM)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(bomService.create).toHaveBeenCalledWith(newBOM)
      expect(result.current.data).toEqual(mockResponse)
    })

    it('should handle create error', async () => {
      const error = new Error('Failed to create BOM')
      vi.mocked(bomService.create).mockRejectedValue(error)

      const { result } = renderHook(() => useCreateBOM(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({
        bom_number: 'BOM002',
        material_id: 1,
        bom_name: 'New BOM',
        bom_type: 'PRODUCTION',
        base_quantity: 1,
        unit_of_measure_id: 1,
      })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useUpdateBOM', () => {
    it('should update BOM successfully', async () => {
      const updateData = {
        bom_name: 'Updated BOM',
        base_quantity: 2,
      }

      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        bom_number: 'BOM001',
        material_id: 1,
        bom_version: 1,
        bom_name: 'Updated BOM',
        bom_type: 'PRODUCTION' as const,
        base_quantity: 2,
        unit_of_measure_id: 1,
        is_active: true,
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(bomService.update).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useUpdateBOM(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 1, ...updateData })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(bomService.update).toHaveBeenCalledWith(1, updateData)
      expect(result.current.data).toEqual(mockResponse)
    })

    it('should handle update error', async () => {
      const error = new Error('Failed to update BOM')
      vi.mocked(bomService.update).mockRejectedValue(error)

      const { result } = renderHook(() => useUpdateBOM(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({ id: 1, bom_name: 'Updated BOM' })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useDeleteBOM', () => {
    it('should delete BOM successfully', async () => {
      vi.mocked(bomService.delete).mockResolvedValue(undefined)

      const { result } = renderHook(() => useDeleteBOM(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(1)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(bomService.delete).toHaveBeenCalledWith(1)
    })
  })
})
