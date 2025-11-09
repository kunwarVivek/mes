import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMaterialMutations } from '../useMaterialMutations'
import { materialService } from '../../services/material.service'
import type { ReactNode } from 'react'

vi.mock('../../services/material.service')

// Mock toast
const mockToast = vi.fn()
vi.mock('@/components/ui/use-toast', () => ({
  toast: (args: unknown) => mockToast(args),
}))

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

describe('useMaterialMutations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createMaterial', () => {
    it('creates material successfully', async () => {
      const createData = {
        organization_id: 1,
        plant_id: 1,
        material_number: 'MAT001',
        material_name: 'Steel Plate',
        material_category_id: 1,
        base_uom_id: 1,
        procurement_type: 'PURCHASE' as const,
        mrp_type: 'MRP' as const,
      }

      const mockResponse = {
        id: 1,
        ...createData,
        safety_stock: 0,
        reorder_point: 0,
        lot_size: 1,
        lead_time_days: 0,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      }

      vi.mocked(materialService.create).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useMaterialMutations(), {
        wrapper: createWrapper(),
      })

      result.current.createMaterial.mutate(createData)

      await waitFor(() => expect(result.current.createMaterial.isSuccess).toBe(true))

      expect(materialService.create).toHaveBeenCalledWith(createData)
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Material created successfully',
      })
    })

    it('handles create errors', async () => {
      const error = {
        response: {
          data: { detail: 'Material number already exists' },
        },
      }

      vi.mocked(materialService.create).mockRejectedValueOnce(error)

      const { result } = renderHook(() => useMaterialMutations(), {
        wrapper: createWrapper(),
      })

      const createData = {
        organization_id: 1,
        plant_id: 1,
        material_number: 'MAT001',
        material_name: 'Steel Plate',
        material_category_id: 1,
        base_uom_id: 1,
        procurement_type: 'PURCHASE' as const,
        mrp_type: 'MRP' as const,
      }

      result.current.createMaterial.mutate(createData)

      await waitFor(() => expect(result.current.createMaterial.isError).toBe(true))

      expect(mockToast).toHaveBeenCalledWith({
        title: 'Failed to create material',
        description: 'Material number already exists',
        variant: 'destructive',
      })
    })
  })

  describe('updateMaterial', () => {
    it('updates material successfully', async () => {
      const updateData = {
        material_name: 'Updated Name',
        description: 'Updated description',
      }

      const mockResponse = {
        id: 1,
        material_number: 'MAT001',
        material_name: 'Updated Name',
        description: 'Updated description',
        organization_id: 1,
        plant_id: 1,
        material_category_id: 1,
        base_uom_id: 1,
        procurement_type: 'PURCHASE',
        mrp_type: 'MRP',
        safety_stock: 0,
        reorder_point: 0,
        lot_size: 1,
        lead_time_days: 0,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-02T00:00:00Z',
      }

      vi.mocked(materialService.update).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useMaterialMutations(), {
        wrapper: createWrapper(),
      })

      result.current.updateMaterial.mutate({ id: 1, data: updateData })

      await waitFor(() => expect(result.current.updateMaterial.isSuccess).toBe(true))

      expect(materialService.update).toHaveBeenCalledWith(1, updateData)
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Material updated successfully',
      })
    })

    it('handles update errors', async () => {
      const error = {
        response: {
          data: { detail: 'Material not found' },
        },
      }

      vi.mocked(materialService.update).mockRejectedValueOnce(error)

      const { result } = renderHook(() => useMaterialMutations(), {
        wrapper: createWrapper(),
      })

      result.current.updateMaterial.mutate({
        id: 999,
        data: { material_name: 'Test' },
      })

      await waitFor(() => expect(result.current.updateMaterial.isError).toBe(true))

      expect(mockToast).toHaveBeenCalledWith({
        title: 'Failed to update material',
        description: 'Material not found',
        variant: 'destructive',
      })
    })
  })

  describe('deleteMaterial', () => {
    it('deletes material successfully', async () => {
      vi.mocked(materialService.delete).mockResolvedValueOnce()

      const { result } = renderHook(() => useMaterialMutations(), {
        wrapper: createWrapper(),
      })

      result.current.deleteMaterial.mutate(1)

      await waitFor(() => expect(result.current.deleteMaterial.isSuccess).toBe(true))

      expect(materialService.delete).toHaveBeenCalledWith(1)
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Material deleted successfully',
      })
    })

    it('handles delete errors', async () => {
      const error = {
        response: {
          data: { detail: 'Cannot delete material with existing inventory' },
        },
      }

      vi.mocked(materialService.delete).mockRejectedValueOnce(error)

      const { result } = renderHook(() => useMaterialMutations(), {
        wrapper: createWrapper(),
      })

      result.current.deleteMaterial.mutate(1)

      await waitFor(() => expect(result.current.deleteMaterial.isError).toBe(true))

      expect(mockToast).toHaveBeenCalledWith({
        title: 'Failed to delete material',
        description: 'Cannot delete material with existing inventory',
        variant: 'destructive',
      })
    })
  })

  it('invalidates queries after successful mutations', async () => {
    const queryClient = new QueryClient()
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    vi.mocked(materialService.create).mockResolvedValueOnce({
      id: 1,
      material_number: 'MAT001',
      material_name: 'Test',
      organization_id: 1,
      plant_id: 1,
      material_category_id: 1,
      base_uom_id: 1,
      procurement_type: 'PURCHASE',
      mrp_type: 'MRP',
      safety_stock: 0,
      reorder_point: 0,
      lot_size: 1,
      lead_time_days: 0,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z',
    })

    const { result } = renderHook(() => useMaterialMutations(), { wrapper })

    result.current.createMaterial.mutate({
      organization_id: 1,
      plant_id: 1,
      material_number: 'MAT001',
      material_name: 'Test',
      material_category_id: 1,
      base_uom_id: 1,
      procurement_type: 'PURCHASE',
      mrp_type: 'MRP',
    })

    await waitFor(() => expect(result.current.createMaterial.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['materials'] })
  })
})
