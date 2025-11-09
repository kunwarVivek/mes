/**
 * Work Order Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { workOrderService } from '../services/workOrder.service'
import type { CreateWorkOrderDTO, UpdateWorkOrderDTO } from '../types/workOrder.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('workOrderService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all work orders without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              work_order_number: 'WO001',
              material_id: 1,
              order_type: 'PRODUCTION',
              order_status: 'PLANNED',
              planned_quantity: 100,
              actual_quantity: 0,
              priority: 5,
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

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await workOrderService.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/work-orders', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch work orders with filters', async () => {
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
        status: 'PLANNED' as const,
        material_id: 1,
        page: 1,
        page_size: 20,
      }

      const result = await workOrderService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/work-orders', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getById', () => {
    it('should fetch work order by ID', async () => {
      const mockWorkOrder = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        work_order_number: 'WO001',
        material_id: 1,
        order_type: 'PRODUCTION',
        order_status: 'PLANNED',
        planned_quantity: 100,
        actual_quantity: 0,
        priority: 5,
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        operations: [],
        materials: [],
      }

      mockedAxios.get.mockResolvedValue({ data: mockWorkOrder })

      const result = await workOrderService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/work-orders/1')
      expect(result).toEqual(mockWorkOrder)
    })
  })

  describe('create', () => {
    it('should create a new work order', async () => {
      const newWorkOrder: CreateWorkOrderDTO = {
        material_id: 1,
        order_type: 'PRODUCTION',
        planned_quantity: 100,
        start_date_planned: '2024-01-01T00:00:00Z',
        end_date_planned: '2024-01-10T00:00:00Z',
        priority: 5,
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_number: 'WO001',
          ...newWorkOrder,
          actual_quantity: 0,
          order_status: 'PLANNED',
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await workOrderService.create(newWorkOrder)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/work-orders', newWorkOrder)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('update', () => {
    it('should update an existing work order', async () => {
      const updateData: UpdateWorkOrderDTO = {
        planned_quantity: 150,
        priority: 8,
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_number: 'WO001',
          material_id: 1,
          order_type: 'PRODUCTION',
          order_status: 'PLANNED',
          planned_quantity: 150,
          actual_quantity: 0,
          priority: 8,
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      }

      mockedAxios.put.mockResolvedValue(mockResponse)

      const result = await workOrderService.update(1, updateData)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/work-orders/1', updateData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('delete', () => {
    it('should cancel a work order', async () => {
      mockedAxios.delete.mockResolvedValue({ data: null })

      await workOrderService.delete(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/work-orders/1')
    })
  })

  describe('release', () => {
    it('should release a work order', async () => {
      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_number: 'WO001',
          material_id: 1,
          order_type: 'PRODUCTION',
          order_status: 'RELEASED',
          planned_quantity: 100,
          actual_quantity: 0,
          priority: 5,
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await workOrderService.release(1)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/work-orders/1/release')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('start', () => {
    it('should start a work order', async () => {
      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_number: 'WO001',
          material_id: 1,
          order_type: 'PRODUCTION',
          order_status: 'IN_PROGRESS',
          planned_quantity: 100,
          actual_quantity: 0,
          priority: 5,
          created_by_user_id: 1,
          start_date_actual: '2024-01-02T00:00:00Z',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await workOrderService.start(1)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/work-orders/1/start')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('complete', () => {
    it('should complete a work order', async () => {
      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          work_order_number: 'WO001',
          material_id: 1,
          order_type: 'PRODUCTION',
          order_status: 'COMPLETED',
          planned_quantity: 100,
          actual_quantity: 100,
          priority: 5,
          created_by_user_id: 1,
          start_date_actual: '2024-01-02T00:00:00Z',
          end_date_actual: '2024-01-10T00:00:00Z',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-10T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await workOrderService.complete(1)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/work-orders/1/complete')
      expect(result).toEqual(mockResponse.data)
    })
  })
})
