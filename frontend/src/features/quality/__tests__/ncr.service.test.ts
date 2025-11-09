/**
 * NCR Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { ncrService } from '../services/ncr.service'
import type { CreateNCRDTO, UpdateNCRDTO } from '../types/ncr.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('ncrService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all NCRs without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              ncr_number: 'NCR-2025-001',
              status: 'OPEN',
              defect_type: 'MATERIAL',
              work_order_id: 1,
              material_id: 1,
              quantity_affected: 50,
              description: 'Material defect found',
              root_cause: null,
              corrective_action: null,
              preventive_action: null,
              reported_by: 1,
              assigned_to: null,
              reported_at: '2025-01-01T10:00:00Z',
              closed_at: null,
              created_at: '2025-01-01T10:00:00Z',
              updated_at: null,
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await ncrService.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/ncr', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch NCRs with filters', async () => {
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
        status: 'OPEN' as const,
        defect_type: 'MATERIAL' as const,
        plant_id: 1,
        page: 1,
        page_size: 20,
      }

      const result = await ncrService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/ncr', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getById', () => {
    it('should fetch NCR by ID', async () => {
      const mockNCR = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        ncr_number: 'NCR-2025-001',
        status: 'OPEN',
        defect_type: 'MATERIAL',
        work_order_id: 1,
        material_id: 1,
        quantity_affected: 50,
        description: 'Material defect found',
        root_cause: null,
        corrective_action: null,
        preventive_action: null,
        reported_by: 1,
        assigned_to: null,
        reported_at: '2025-01-01T10:00:00Z',
        closed_at: null,
        created_at: '2025-01-01T10:00:00Z',
        updated_at: null,
      }

      mockedAxios.get.mockResolvedValue({ data: mockNCR })

      const result = await ncrService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/ncr/1')
      expect(result).toEqual(mockNCR)
    })
  })

  describe('create', () => {
    it('should create a new NCR', async () => {
      const newNCR: CreateNCRDTO = {
        organization_id: 1,
        plant_id: 1,
        ncr_number: 'NCR-2025-001',
        defect_type: 'MATERIAL',
        work_order_id: 1,
        material_id: 1,
        quantity_affected: 50,
        description: 'Material defect found',
        reported_by: 1,
      }

      const mockResponse = {
        data: {
          id: 1,
          ...newNCR,
          status: 'OPEN',
          root_cause: null,
          corrective_action: null,
          preventive_action: null,
          assigned_to: null,
          reported_at: '2025-01-01T10:00:00Z',
          closed_at: null,
          created_at: '2025-01-01T10:00:00Z',
          updated_at: null,
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await ncrService.create(newNCR)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/ncr', newNCR)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('update', () => {
    it('should update an existing NCR', async () => {
      const updateData: UpdateNCRDTO = {
        status: 'INVESTIGATING',
        root_cause: 'Poor quality raw material',
        corrective_action: 'Reject batch and reorder',
        assigned_to: 2,
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          ncr_number: 'NCR-2025-001',
          status: 'INVESTIGATING',
          defect_type: 'MATERIAL',
          work_order_id: 1,
          material_id: 1,
          quantity_affected: 50,
          description: 'Material defect found',
          root_cause: 'Poor quality raw material',
          corrective_action: 'Reject batch and reorder',
          preventive_action: null,
          reported_by: 1,
          assigned_to: 2,
          reported_at: '2025-01-01T10:00:00Z',
          closed_at: null,
          created_at: '2025-01-01T10:00:00Z',
          updated_at: '2025-01-01T12:00:00Z',
        },
      }

      mockedAxios.put.mockResolvedValue(mockResponse)

      const result = await ncrService.update(1, updateData)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/ncr/1', updateData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('delete', () => {
    it('should delete an NCR', async () => {
      mockedAxios.delete.mockResolvedValue({ data: null })

      await ncrService.delete(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/ncr/1')
    })
  })
})
