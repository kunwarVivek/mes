/**
 * BOM Service Tests
 *
 * TDD: Testing API service layer with mocked apiClient
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { bomService } from '../services/bom.service'
import type { CreateBOMDTO, UpdateBOMDTO } from '../types/bom.types'

vi.mock('../../../lib/api-client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import apiClient from '../../../lib/api-client'
const mockedApiClient = vi.mocked(apiClient)

describe('bomService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all BOMs without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              bom_number: 'BOM001',
              material_id: 1,
              bom_version: 1,
              bom_name: 'Test BOM',
              bom_type: 'PRODUCTION',
              base_quantity: 1,
              unit_of_measure_id: 1,
              is_active: true,
              created_by_user_id: 1,
              created_at: '2024-01-01T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 50,
          total_pages: 1,
        },
      }

      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await bomService.getAll()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/boms', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch BOMs with filters', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0,
        },
      }

      mockedApiClient.get.mockResolvedValue(mockResponse)

      const filters = {
        material_id: 1,
        bom_type: 'PRODUCTION' as const,
        page: 1,
        page_size: 20,
      }

      const result = await bomService.getAll(filters)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/boms', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getById', () => {
    it('should fetch BOM by ID', async () => {
      const mockBOM = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        bom_number: 'BOM001',
        material_id: 1,
        bom_version: 1,
        bom_name: 'Test BOM',
        bom_type: 'PRODUCTION',
        base_quantity: 1,
        unit_of_measure_id: 1,
        is_active: true,
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        bom_lines: [],
      }

      mockedApiClient.get.mockResolvedValue({ data: mockBOM })

      const result = await bomService.getById(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/boms/1')
      expect(result).toEqual(mockBOM)
    })
  })

  describe('create', () => {
    it('should create a new BOM', async () => {
      const newBOM: CreateBOMDTO = {
        bom_number: 'BOM002',
        material_id: 1,
        bom_name: 'New BOM',
        bom_type: 'PRODUCTION',
        base_quantity: 1,
        unit_of_measure_id: 1,
        bom_version: 1,
      }

      const mockResponse = {
        data: {
          id: 2,
          organization_id: 1,
          plant_id: 1,
          ...newBOM,
          is_active: true,
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      }

      mockedApiClient.post.mockResolvedValue(mockResponse)

      const result = await bomService.create(newBOM)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/boms', newBOM)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('update', () => {
    it('should update an existing BOM', async () => {
      const updateData: UpdateBOMDTO = {
        bom_name: 'Updated BOM',
        base_quantity: 2,
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          bom_number: 'BOM001',
          material_id: 1,
          bom_version: 1,
          bom_name: 'Updated BOM',
          bom_type: 'PRODUCTION',
          base_quantity: 2,
          unit_of_measure_id: 1,
          is_active: true,
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      }

      mockedApiClient.put.mockResolvedValue(mockResponse)

      const result = await bomService.update(1, updateData)

      expect(mockedApiClient.put).toHaveBeenCalledWith('/boms/1', updateData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('delete', () => {
    it('should delete a BOM', async () => {
      mockedApiClient.delete.mockResolvedValue({ data: null })

      await bomService.delete(1)

      expect(mockedApiClient.delete).toHaveBeenCalledWith('/boms/1')
    })
  })

  describe('search', () => {
    it('should search BOMs by query', async () => {
      const mockResults = [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          bom_number: 'BOM001',
          material_id: 1,
          bom_version: 1,
          bom_name: 'Test BOM',
          bom_type: 'PRODUCTION',
          base_quantity: 1,
          unit_of_measure_id: 1,
          is_active: true,
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      mockedApiClient.get.mockResolvedValue({ data: mockResults })

      const result = await bomService.search('test', 20)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/boms/search', {
        params: { q: 'test', limit: 20 },
      })
      expect(result).toEqual(mockResults)
    })
  })
})
