/**
 * Material Mutation Hooks Tests
 *
 * TDD: Testing create, update, delete mutation hooks
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCreateMaterial } from '../hooks/useCreateMaterial'
import { useUpdateMaterial } from '../hooks/useUpdateMaterial'
import { useDeleteMaterial } from '../hooks/useDeleteMaterial'
import { materialService } from '../services/material.service'
import type { ReactNode } from 'react'
import type { CreateMaterialDTO, UpdateMaterialDTO } from '../types/material.types'

vi.mock('../services/material.service')

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

describe('useCreateMaterial', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create material successfully', async () => {
    const newMaterial: CreateMaterialDTO = {
      organization_id: 1,
      plant_id: 1,
      material_number: 'MAT001',
      material_name: 'Test Material',
      material_category_id: 1,
      base_uom_id: 1,
      procurement_type: 'PURCHASE',
      mrp_type: 'MRP',
    }

    const createdMaterial = {
      ...newMaterial,
      id: 1,
      safety_stock: 0,
      reorder_point: 0,
      lot_size: 1,
      lead_time_days: 0,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(materialService.create).mockResolvedValue(createdMaterial)

    const { result } = renderHook(() => useCreateMaterial(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(newMaterial)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdMaterial)
    expect(materialService.create).toHaveBeenCalledWith(newMaterial)
  })

  it('should handle creation errors', async () => {
    const error = new Error('Failed to create material')
    vi.mocked(materialService.create).mockRejectedValue(error)

    const { result } = renderHook(() => useCreateMaterial(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      organization_id: 1,
      plant_id: 1,
      material_number: 'MAT001',
      material_name: 'Test Material',
      material_category_id: 1,
      base_uom_id: 1,
      procurement_type: 'PURCHASE',
      mrp_type: 'MRP',
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})

describe('useUpdateMaterial', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update material successfully', async () => {
    const updateData: UpdateMaterialDTO = {
      material_name: 'Updated Material',
      safety_stock: 200,
    }

    const updatedMaterial = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      material_number: 'MAT001',
      material_name: 'Updated Material',
      material_category_id: 1,
      base_uom_id: 1,
      procurement_type: 'PURCHASE' as const,
      mrp_type: 'MRP' as const,
      safety_stock: 200,
      reorder_point: 50,
      lot_size: 10,
      lead_time_days: 5,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    }

    vi.mocked(materialService.update).mockResolvedValue(updatedMaterial)

    const { result } = renderHook(() => useUpdateMaterial(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ id: 1, data: updateData })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedMaterial)
    expect(materialService.update).toHaveBeenCalledWith(1, updateData)
  })
})

describe('useDeleteMaterial', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should delete material successfully', async () => {
    vi.mocked(materialService.delete).mockResolvedValue(undefined)

    const { result } = renderHook(() => useDeleteMaterial(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(materialService.delete).toHaveBeenCalledWith(1)
  })

  it('should handle deletion errors', async () => {
    const error = new Error('Failed to delete material')
    vi.mocked(materialService.delete).mockRejectedValue(error)

    const { result } = renderHook(() => useDeleteMaterial(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })
})
