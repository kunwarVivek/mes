import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ncrService } from '../ncr.service'
import apiClient from '@/lib/api-client'
import type { CreateNCRFormData, UpdateNCRStatusFormData } from '../../schemas/ncr.schema'

vi.mock('@/lib/api-client')

describe('ncrService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('list', () => {
    it('fetches NCR list without filters', async () => {
      const mockResponse = {
        items: [
          {
            id: 1,
            ncr_number: 'NCR-2024-001',
            status: 'OPEN',
            work_order_id: 1,
            material_id: 1,
          },
        ],
        total: 1,
        page: 1,
        page_size: 25,
        total_pages: 1,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const result = await ncrService.list()

      expect(apiClient.get).toHaveBeenCalledWith('/quality/ncrs', { params: undefined })
      expect(result).toEqual(mockResponse)
    })

    it('fetches NCR list with status filter', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 25,
        total_pages: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const params = { status: 'OPEN' }
      await ncrService.list(params)

      expect(apiClient.get).toHaveBeenCalledWith('/quality/ncrs', { params })
    })

    it('fetches NCR list with work_order_id filter', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 25,
        total_pages: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const params = { work_order_id: 123 }
      await ncrService.list(params)

      expect(apiClient.get).toHaveBeenCalledWith('/quality/ncrs', { params })
    })

    it('fetches NCR list with pagination', async () => {
      const mockResponse = {
        items: [],
        total: 50,
        page: 2,
        page_size: 10,
        total_pages: 5,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const params = { page: 2, page_size: 10 }
      await ncrService.list(params)

      expect(apiClient.get).toHaveBeenCalledWith('/quality/ncrs', { params })
    })

    it('fetches NCR list with multiple filters', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 25,
        total_pages: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const params = { status: 'RESOLVED', work_order_id: 456, page: 1, page_size: 25 }
      await ncrService.list(params)

      expect(apiClient.get).toHaveBeenCalledWith('/quality/ncrs', { params })
    })
  })

  describe('get', () => {
    it('fetches NCR by ID', async () => {
      const mockNCR = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        ncr_number: 'NCR-2024-001',
        work_order_id: 1,
        material_id: 1,
        defect_type: 'DIMENSIONAL',
        defect_description: 'Part dimensions out of tolerance',
        quantity_defective: 5,
        status: 'OPEN',
        reported_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockNCR })

      const result = await ncrService.get(1)

      expect(apiClient.get).toHaveBeenCalledWith('/quality/ncrs/1')
      expect(result).toEqual(mockNCR)
    })

    it('fetches NCR with attachments', async () => {
      const mockNCR = {
        id: 2,
        ncr_number: 'NCR-2024-002',
        attachment_urls: ['https://example.com/photo1.jpg', 'https://example.com/photo2.jpg'],
        status: 'IN_REVIEW',
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockNCR })

      const result = await ncrService.get(2)

      expect(apiClient.get).toHaveBeenCalledWith('/quality/ncrs/2')
      expect(result.attachment_urls).toHaveLength(2)
    })
  })

  describe('create', () => {
    it('creates new NCR', async () => {
      const ncrData: CreateNCRFormData = {
        ncr_number: 'NCR-2024-001',
        work_order_id: 1,
        material_id: 1,
        defect_type: 'DIMENSIONAL',
        defect_description: 'Part dimensions out of tolerance',
        quantity_defective: 5,
        reported_by_user_id: 1,
      }

      const mockResponse = {
        id: 1,
        ...ncrData,
        organization_id: 1,
        plant_id: 1,
        status: 'OPEN',
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await ncrService.create(ncrData)

      expect(apiClient.post).toHaveBeenCalledWith('/quality/ncrs', ncrData)
      expect(result).toEqual(mockResponse)
      expect(result.status).toBe('OPEN')
    })

    it('creates NCR with attachments', async () => {
      const ncrData: CreateNCRFormData = {
        ncr_number: 'NCR-2024-002',
        work_order_id: 2,
        material_id: 2,
        defect_type: 'VISUAL',
        defect_description: 'Surface defects detected',
        quantity_defective: 10,
        reported_by_user_id: 1,
        attachment_urls: ['https://example.com/photo1.jpg'],
      }

      const mockResponse = {
        id: 2,
        ...ncrData,
        organization_id: 1,
        plant_id: 1,
        status: 'OPEN',
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await ncrService.create(ncrData)

      expect(apiClient.post).toHaveBeenCalledWith('/quality/ncrs', ncrData)
      expect(result.attachment_urls).toBeDefined()
    })
  })

  describe('updateStatus', () => {
    it('updates NCR status to IN_REVIEW', async () => {
      const statusUpdate: UpdateNCRStatusFormData = {
        status: 'IN_REVIEW',
      }

      const mockResponse = {
        id: 1,
        ncr_number: 'NCR-2024-001',
        status: 'IN_REVIEW',
        work_order_id: 1,
        material_id: 1,
        defect_type: 'DIMENSIONAL',
        defect_description: 'Part dimensions out of tolerance',
        quantity_defective: 5,
        reported_by_user_id: 1,
        organization_id: 1,
        plant_id: 1,
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(apiClient.patch).mockResolvedValue({ data: mockResponse })

      const result = await ncrService.updateStatus(1, statusUpdate)

      expect(apiClient.patch).toHaveBeenCalledWith('/quality/ncrs/1/status', statusUpdate)
      expect(result.status).toBe('IN_REVIEW')
    })

    it('updates NCR status to RESOLVED with resolution notes', async () => {
      const statusUpdate: UpdateNCRStatusFormData = {
        status: 'RESOLVED',
        resolution_notes: 'Parts reworked and reinspected',
        resolved_by_user_id: 2,
      }

      const mockResponse = {
        id: 1,
        status: 'RESOLVED',
        resolution_notes: 'Parts reworked and reinspected',
        resolved_by_user_id: 2,
        resolved_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(apiClient.patch).mockResolvedValue({ data: mockResponse })

      const result = await ncrService.updateStatus(1, statusUpdate)

      expect(apiClient.patch).toHaveBeenCalledWith('/quality/ncrs/1/status', statusUpdate)
      expect(result.status).toBe('RESOLVED')
      expect(result.resolution_notes).toBe('Parts reworked and reinspected')
      expect(result.resolved_by_user_id).toBe(2)
    })

    it('updates NCR status to CLOSED', async () => {
      const statusUpdate: UpdateNCRStatusFormData = {
        status: 'CLOSED',
      }

      const mockResponse = {
        id: 1,
        status: 'CLOSED',
      }

      vi.mocked(apiClient.patch).mockResolvedValue({ data: mockResponse })

      const result = await ncrService.updateStatus(1, statusUpdate)

      expect(apiClient.patch).toHaveBeenCalledWith('/quality/ncrs/1/status', statusUpdate)
      expect(result.status).toBe('CLOSED')
    })
  })
})
