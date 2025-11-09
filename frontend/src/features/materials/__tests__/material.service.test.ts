/**
 * Material Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { materialService } from '../services/material.service'
import type { CreateMaterialDTO, UpdateMaterialDTO } from '../types/material.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('materialService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all materials without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              material_number: 'MAT001',
              material_name: 'Test Material',
              material_category_id: 1,
              base_uom_id: 1,
              procurement_type: 'PURCHASE',
              mrp_type: 'MRP',
              safety_stock: 100,
              reorder_point: 50,
              lot_size: 10,
              lead_time_days: 5,
              is_active: true,
              created_at: '2024-01-01T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 50,
          total_pages: 1,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await materialService.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/materials', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch materials with filters', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const filters = {
        category_id: 1,
        procurement_type: 'PURCHASE' as const,
        page: 1,
        page_size: 20,
      }

      const result = await materialService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/materials', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getById', () => {
    it('should fetch material by ID', async () => {
      const mockMaterial = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        material_number: 'MAT001',
        material_name: 'Test Material',
        material_category_id: 1,
        base_uom_id: 1,
        procurement_type: 'PURCHASE',
        mrp_type: 'MRP',
        safety_stock: 100,
        reorder_point: 50,
        lot_size: 10,
        lead_time_days: 5,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }

      mockedAxios.get.mockResolvedValue({ data: mockMaterial })

      const result = await materialService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/materials/1')
      expect(result).toEqual(mockMaterial)
    })
  })

  describe('create', () => {
    it('should create a new material', async () => {
      const newMaterial: CreateMaterialDTO = {
        organization_id: 1,
        plant_id: 1,
        material_number: 'MAT002',
        material_name: 'New Material',
        material_category_id: 1,
        base_uom_id: 1,
        procurement_type: 'MANUFACTURE',
        mrp_type: 'MRP',
        safety_stock: 50,
        reorder_point: 25,
        lot_size: 5,
        lead_time_days: 3,
      }

      const mockResponse = {
        data: {
          ...newMaterial,
          id: 2,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await materialService.create(newMaterial)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/materials', newMaterial)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('update', () => {
    it('should update an existing material', async () => {
      const updateData: UpdateMaterialDTO = {
        material_name: 'Updated Material',
        safety_stock: 200,
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          material_number: 'MAT001',
          material_name: 'Updated Material',
          material_category_id: 1,
          base_uom_id: 1,
          procurement_type: 'PURCHASE',
          mrp_type: 'MRP',
          safety_stock: 200,
          reorder_point: 50,
          lot_size: 10,
          lead_time_days: 5,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      }

      mockedAxios.put.mockResolvedValue(mockResponse)

      const result = await materialService.update(1, updateData)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/materials/1', updateData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('delete', () => {
    it('should delete a material', async () => {
      mockedAxios.delete.mockResolvedValue({ data: null })

      await materialService.delete(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/materials/1')
    })
  })

  describe('search', () => {
    it('should search materials by query', async () => {
      const mockResults = [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          material_number: 'MAT001',
          material_name: 'Test Material',
          material_category_id: 1,
          base_uom_id: 1,
          procurement_type: 'PURCHASE',
          mrp_type: 'MRP',
          safety_stock: 100,
          reorder_point: 50,
          lot_size: 10,
          lead_time_days: 5,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      mockedAxios.get.mockResolvedValue({ data: mockResults })

      const result = await materialService.search('test', 20)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/materials/search', {
        params: { q: 'test', limit: 20 },
      })
      expect(result).toEqual(mockResults)
    })
  })
})
