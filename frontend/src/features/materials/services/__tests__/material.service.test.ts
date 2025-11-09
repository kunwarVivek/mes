import { describe, it, expect, vi, beforeEach } from 'vitest'
import { materialService } from '../material.service'
import apiClient from '@/lib/api-client'

vi.mock('@/lib/api-client')

describe('materialService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('list', () => {
    it('fetches materials with default params', async () => {
      const mockResponse = {
        items: [
          {
            id: 1,
            material_number: 'MAT001',
            material_name: 'Steel Plate',
            procurement_type: 'PURCHASE',
            mrp_type: 'MRP',
          },
        ],
        total: 1,
        page: 1,
        page_size: 25,
        total_pages: 1,
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      const result = await materialService.list()

      expect(apiClient.get).toHaveBeenCalledWith('/materials', { params: undefined })
      expect(result).toEqual(mockResponse)
    })

    it('fetches materials with pagination params', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 2,
        page_size: 10,
        total_pages: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      await materialService.list({ page: 2, page_size: 10 })

      expect(apiClient.get).toHaveBeenCalledWith('/materials', {
        params: { page: 2, page_size: 10 },
      })
    })

    it('fetches materials with search query', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 25,
        total_pages: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      await materialService.list({ search: 'steel' })

      expect(apiClient.get).toHaveBeenCalledWith('/materials', {
        params: { search: 'steel' },
      })
    })

    it('fetches materials with procurement type filter', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 25,
        total_pages: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      await materialService.list({ procurement_type: 'PURCHASE' })

      expect(apiClient.get).toHaveBeenCalledWith('/materials', {
        params: { procurement_type: 'PURCHASE' },
      })
    })

    it('handles API errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('Network error'))

      await expect(materialService.list()).rejects.toThrow('Network error')
    })
  })

  describe('get', () => {
    it('fetches a single material by id', async () => {
      const mockMaterial = {
        id: 1,
        material_number: 'MAT001',
        material_name: 'Steel Plate',
        procurement_type: 'PURCHASE',
        mrp_type: 'MRP',
        organization_id: 1,
        plant_id: 1,
        material_category_id: 1,
        base_uom_id: 1,
        created_at: '2025-01-01T00:00:00Z',
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockMaterial })

      const result = await materialService.get(1)

      expect(apiClient.get).toHaveBeenCalledWith('/materials/1')
      expect(result).toEqual(mockMaterial)
    })

    it('handles 404 errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce({
        response: { status: 404, data: { detail: 'Material not found' } },
      })

      await expect(materialService.get(999)).rejects.toMatchObject({
        response: { status: 404 },
      })
    })
  })

  describe('create', () => {
    it('creates a new material', async () => {
      const createData = {
        organization_id: 1,
        plant_id: 1,
        material_number: 'MAT001',
        material_name: 'Steel Plate',
        material_category_id: 1,
        base_uom_id: 1,
        procurement_type: 'PURCHASE',
        mrp_type: 'MRP',
      }

      const mockResponse = {
        id: 1,
        ...createData,
        created_at: '2025-01-01T00:00:00Z',
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await materialService.create(createData)

      expect(apiClient.post).toHaveBeenCalledWith('/materials', createData)
      expect(result).toEqual(mockResponse)
    })

    it('handles validation errors', async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce({
        response: {
          status: 422,
          data: { detail: [{ loc: ['material_number'], msg: 'Invalid format' }] },
        },
      })

      await expect(
        materialService.create({
          organization_id: 1,
          plant_id: 1,
          material_number: 'invalid',
          material_name: 'Test',
          material_category_id: 1,
          base_uom_id: 1,
          procurement_type: 'PURCHASE',
          mrp_type: 'MRP',
        })
      ).rejects.toMatchObject({
        response: { status: 422 },
      })
    })
  })

  describe('update', () => {
    it('updates an existing material', async () => {
      const updateData = {
        material_name: 'Updated Name',
        description: 'Updated description',
      }

      const mockResponse = {
        id: 1,
        material_number: 'MAT001',
        material_name: 'Updated Name',
        description: 'Updated description',
        procurement_type: 'PURCHASE',
        mrp_type: 'MRP',
        organization_id: 1,
        plant_id: 1,
        material_category_id: 1,
        base_uom_id: 1,
        updated_at: '2025-01-01T00:00:00Z',
      }

      vi.mocked(apiClient.put).mockResolvedValueOnce({ data: mockResponse })

      const result = await materialService.update(1, updateData)

      expect(apiClient.put).toHaveBeenCalledWith('/materials/1', updateData)
      expect(result).toEqual(mockResponse)
    })

    it('handles partial updates', async () => {
      const updateData = { is_active: false }

      vi.mocked(apiClient.put).mockResolvedValueOnce({
        data: { id: 1, is_active: false },
      })

      await materialService.update(1, updateData)

      expect(apiClient.put).toHaveBeenCalledWith('/materials/1', updateData)
    })
  })

  describe('delete', () => {
    it('deletes a material', async () => {
      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: null })

      await materialService.delete(1)

      expect(apiClient.delete).toHaveBeenCalledWith('/materials/1')
    })

    it('handles 404 errors on delete', async () => {
      vi.mocked(apiClient.delete).mockRejectedValueOnce({
        response: { status: 404 },
      })

      await expect(materialService.delete(999)).rejects.toMatchObject({
        response: { status: 404 },
      })
    })
  })
})
