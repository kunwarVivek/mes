import { describe, it, expect, vi, beforeEach } from 'vitest'
import { workOrderService } from '../work-order.service'
import apiClient from '@/lib/api-client'

vi.mock('@/lib/api-client')

describe('workOrderService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('list', () => {
    it('calls API with correct endpoint and params', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const params = { page: 1, page_size: 10, status: 'PLANNED' }
      const result = await workOrderService.list(params)

      expect(apiClient.get).toHaveBeenCalledWith('/work-orders', { params })
      expect(result).toEqual(mockResponse)
    })

    it('calls API without params when none provided', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      await workOrderService.list()

      expect(apiClient.get).toHaveBeenCalledWith('/work-orders', { params: undefined })
    })
  })

  describe('get', () => {
    it('calls API with correct endpoint', async () => {
      const mockWorkOrder = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'PLANNED',
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockWorkOrder })

      const result = await workOrderService.get(1)

      expect(apiClient.get).toHaveBeenCalledWith('/work-orders/1')
      expect(result).toEqual(mockWorkOrder)
    })
  })

  describe('create', () => {
    it('calls API with correct endpoint and data', async () => {
      const createData = {
        material_id: 1,
        order_type: 'PRODUCTION' as const,
        planned_quantity: 100,
        priority: 5,
      }

      const mockResponse = {
        id: 1,
        work_order_number: 'WO-2025-001',
        ...createData,
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await workOrderService.create(createData)

      expect(apiClient.post).toHaveBeenCalledWith('/work-orders', createData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('update', () => {
    it('calls API with correct endpoint and data', async () => {
      const updateData = {
        planned_quantity: 150,
        priority: 7,
      }

      const mockResponse = {
        id: 1,
        work_order_number: 'WO-2025-001',
        ...updateData,
      }

      vi.mocked(apiClient.put).mockResolvedValue({ data: mockResponse })

      const result = await workOrderService.update(1, updateData)

      expect(apiClient.put).toHaveBeenCalledWith('/work-orders/1', updateData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('cancel', () => {
    it('calls API with correct endpoint', async () => {
      const mockResponse = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'CANCELLED',
      }

      vi.mocked(apiClient.delete).mockResolvedValue({ data: mockResponse })

      const result = await workOrderService.cancel(1)

      expect(apiClient.delete).toHaveBeenCalledWith('/work-orders/1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('release', () => {
    it('calls API with correct endpoint for state transition', async () => {
      const mockResponse = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'RELEASED',
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await workOrderService.release(1)

      expect(apiClient.post).toHaveBeenCalledWith('/work-orders/1/release', {})
      expect(result).toEqual(mockResponse)
    })
  })

  describe('start', () => {
    it('calls API with correct endpoint for state transition', async () => {
      const mockResponse = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'IN_PROGRESS',
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await workOrderService.start(1)

      expect(apiClient.post).toHaveBeenCalledWith('/work-orders/1/start', {})
      expect(result).toEqual(mockResponse)
    })
  })

  describe('complete', () => {
    it('calls API with correct endpoint for state transition', async () => {
      const mockResponse = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'COMPLETED',
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await workOrderService.complete(1)

      expect(apiClient.post).toHaveBeenCalledWith('/work-orders/1/complete', {})
      expect(result).toEqual(mockResponse)
    })
  })

  describe('addOperation', () => {
    it('calls API with correct endpoint and operation data', async () => {
      const operationData = {
        operation_sequence: 10,
        operation_name: 'Cutting',
        setup_time_minutes: 30,
        run_time_minutes: 120,
      }

      const mockResponse = {
        id: 1,
        work_order_id: 1,
        ...operationData,
        status: 'PENDING',
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await workOrderService.addOperation(1, operationData)

      expect(apiClient.post).toHaveBeenCalledWith('/work-orders/1/operations', operationData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('addMaterial', () => {
    it('calls API with correct endpoint and material data', async () => {
      const materialData = {
        material_id: 2,
        required_quantity: 50,
      }

      const mockResponse = {
        id: 1,
        work_order_id: 1,
        ...materialData,
        allocated_quantity: 0,
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await workOrderService.addMaterial(1, materialData)

      expect(apiClient.post).toHaveBeenCalledWith('/work-orders/1/materials', materialData)
      expect(result).toEqual(mockResponse)
    })
  })
})
