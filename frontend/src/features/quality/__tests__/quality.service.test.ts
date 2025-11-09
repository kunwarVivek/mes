/**
 * Quality Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { qualityService } from '../services/quality.service'
import type { CreateNCRDTO, UpdateNCRStatusDTO } from '../types/quality.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('qualityService', () => {
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
              ncr_number: 'NCR-2024-001',
              work_order_id: 100,
              material_id: 50,
              defect_type: 'DIMENSIONAL',
              defect_description: 'Part dimension out of tolerance by 0.5mm',
              quantity_defective: 5,
              status: 'OPEN',
              reported_by_user_id: 1,
              attachment_urls: [],
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

      const result = await qualityService.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/quality/ncrs', { params: undefined })
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
        defect_type: 'DIMENSIONAL' as const,
        page: 1,
        page_size: 20,
      }

      const result = await qualityService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/quality/ncrs', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getById', () => {
    it('should fetch NCR by ID', async () => {
      const mockNCR = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        ncr_number: 'NCR-2024-001',
        work_order_id: 100,
        material_id: 50,
        defect_type: 'VISUAL',
        defect_description: 'Surface scratches visible on part',
        quantity_defective: 3,
        status: 'IN_REVIEW',
        reported_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
      }

      mockedAxios.get.mockResolvedValue({ data: mockNCR })

      const result = await qualityService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/quality/ncrs/1')
      expect(result).toEqual(mockNCR)
    })
  })

  describe('create', () => {
    it('should create a new NCR', async () => {
      const newNCR: CreateNCRDTO = {
        ncr_number: 'NCR-2024-002',
        work_order_id: 101,
        material_id: 51,
        defect_type: 'FUNCTIONAL',
        defect_description: 'Component fails functional test at 100Hz',
        quantity_defective: 10,
        reported_by_user_id: 2,
        attachment_urls: ['https://example.com/photo1.jpg'],
      }

      const mockResponse = {
        data: {
          ...newNCR,
          id: 2,
          organization_id: 1,
          plant_id: 1,
          status: 'OPEN',
          created_at: '2024-01-02T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await qualityService.create(newNCR)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/quality/ncrs', newNCR)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('updateStatus', () => {
    it('should update NCR status', async () => {
      const statusUpdate: UpdateNCRStatusDTO = {
        status: 'RESOLVED',
        resolution_notes: 'Parts reworked and passed inspection',
        resolved_by_user_id: 3,
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          ncr_number: 'NCR-2024-001',
          work_order_id: 100,
          material_id: 50,
          defect_type: 'DIMENSIONAL',
          defect_description: 'Part dimension out of tolerance',
          quantity_defective: 5,
          status: 'RESOLVED',
          reported_by_user_id: 1,
          resolution_notes: 'Parts reworked and passed inspection',
          resolved_by_user_id: 3,
          resolved_at: '2024-01-03T00:00:00Z',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-03T00:00:00Z',
        },
      }

      mockedAxios.patch.mockResolvedValue(mockResponse)

      const result = await qualityService.updateStatus(1, statusUpdate)

      expect(mockedAxios.patch).toHaveBeenCalledWith('/api/v1/quality/ncrs/1/status', statusUpdate)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('delete', () => {
    it('should delete an NCR', async () => {
      mockedAxios.delete.mockResolvedValue({ data: null })

      await qualityService.delete(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/quality/ncrs/1')
    })
  })

  describe('review', () => {
    it('should move NCR to review status', async () => {
      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          ncr_number: 'NCR-2024-001',
          work_order_id: 100,
          material_id: 50,
          defect_type: 'MATERIAL',
          defect_description: 'Material contamination detected',
          quantity_defective: 20,
          status: 'IN_REVIEW',
          reported_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      }

      mockedAxios.patch.mockResolvedValue(mockResponse)

      const result = await qualityService.review(1)

      expect(mockedAxios.patch).toHaveBeenCalledWith('/api/v1/quality/ncrs/1/status', {
        status: 'IN_REVIEW',
      })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('resolve', () => {
    it('should resolve an NCR with notes', async () => {
      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          ncr_number: 'NCR-2024-001',
          work_order_id: 100,
          material_id: 50,
          defect_type: 'OTHER',
          defect_description: 'Unspecified quality issue',
          quantity_defective: 1,
          status: 'RESOLVED',
          reported_by_user_id: 1,
          resolution_notes: 'Root cause identified and corrected',
          resolved_by_user_id: 4,
          resolved_at: '2024-01-04T00:00:00Z',
          created_at: '2024-01-01T00:00:00Z',
        },
      }

      mockedAxios.patch.mockResolvedValue(mockResponse)

      const result = await qualityService.resolve(1, 'Root cause identified and corrected', 4)

      expect(mockedAxios.patch).toHaveBeenCalledWith('/api/v1/quality/ncrs/1/status', {
        status: 'RESOLVED',
        resolution_notes: 'Root cause identified and corrected',
        resolved_by_user_id: 4,
      })
      expect(result).toEqual(mockResponse.data)
    })
  })
})
