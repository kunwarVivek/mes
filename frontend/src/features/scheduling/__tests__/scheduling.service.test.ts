/**
 * Scheduling Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { schedulingService } from '../services/scheduling.service'
import type {
  CreateScheduledOperationDTO,
  UpdateScheduledOperationDTO,
} from '../types/scheduling.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('schedulingService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all scheduled operations without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              work_order_id: 1,
              operation_sequence: 10,
              operation_name: 'Cutting',
              machine_id: 1,
              scheduled_start: '2024-01-01T08:00:00Z',
              scheduled_end: '2024-01-01T10:00:00Z',
              status: 'SCHEDULED',
              priority: 5,
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

      const result = await schedulingService.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/scheduled-operations', {
        params: undefined,
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch scheduled operations with filters', async () => {
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
        work_order_id: 1,
        status: 'COMPLETED' as const,
        page: 1,
        page_size: 20,
      }

      const result = await schedulingService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/scheduled-operations', {
        params: filters,
      })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getById', () => {
    it('should fetch scheduled operation by ID', async () => {
      const mockOperation = {
        id: 1,
        organization_id: 1,
        work_order_id: 1,
        operation_sequence: 10,
        operation_name: 'Cutting',
        machine_id: 1,
        scheduled_start: '2024-01-01T08:00:00Z',
        scheduled_end: '2024-01-01T10:00:00Z',
        status: 'SCHEDULED',
        priority: 5,
        created_at: '2024-01-01T00:00:00Z',
      }

      mockedAxios.get.mockResolvedValue({ data: mockOperation })

      const result = await schedulingService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/scheduled-operations/1')
      expect(result).toEqual(mockOperation)
    })
  })

  describe('create', () => {
    it('should create a new scheduled operation', async () => {
      const newOperation: CreateScheduledOperationDTO = {
        organization_id: 1,
        work_order_id: 1,
        operation_sequence: 20,
        operation_name: 'Assembly',
        machine_id: 2,
        scheduled_start: '2024-01-01T10:00:00Z',
        scheduled_end: '2024-01-01T12:00:00Z',
        status: 'SCHEDULED',
        priority: 7,
      }

      const mockResponse = {
        data: {
          ...newOperation,
          id: 2,
          created_at: '2024-01-01T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await schedulingService.create(newOperation)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/scheduled-operations', newOperation)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('update', () => {
    it('should update an existing scheduled operation', async () => {
      const updateData: UpdateScheduledOperationDTO = {
        operation_name: 'Updated Assembly',
        priority: 9,
        status: 'IN_PROGRESS',
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          work_order_id: 1,
          operation_sequence: 10,
          operation_name: 'Updated Assembly',
          machine_id: 1,
          scheduled_start: '2024-01-01T08:00:00Z',
          scheduled_end: '2024-01-01T10:00:00Z',
          actual_start: '2024-01-01T08:05:00Z',
          status: 'IN_PROGRESS',
          priority: 9,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T08:05:00Z',
        },
      }

      mockedAxios.put.mockResolvedValue(mockResponse)

      const result = await schedulingService.update(1, updateData)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/scheduled-operations/1', updateData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('delete', () => {
    it('should delete a scheduled operation', async () => {
      mockedAxios.delete.mockResolvedValue({ data: null })

      await schedulingService.delete(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/scheduled-operations/1')
    })
  })

  describe('getByWorkOrder', () => {
    it('should fetch operations by work order ID', async () => {
      const mockOperations = [
        {
          id: 1,
          organization_id: 1,
          work_order_id: 1,
          operation_sequence: 10,
          operation_name: 'Cutting',
          machine_id: 1,
          scheduled_start: '2024-01-01T08:00:00Z',
          scheduled_end: '2024-01-01T10:00:00Z',
          status: 'SCHEDULED',
          priority: 5,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          organization_id: 1,
          work_order_id: 1,
          operation_sequence: 20,
          operation_name: 'Assembly',
          machine_id: 2,
          scheduled_start: '2024-01-01T10:00:00Z',
          scheduled_end: '2024-01-01T12:00:00Z',
          status: 'SCHEDULED',
          priority: 5,
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      mockedAxios.get.mockResolvedValue({ data: mockOperations })

      const result = await schedulingService.getByWorkOrder(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/scheduled-operations/work-order/1')
      expect(result).toEqual(mockOperations)
    })
  })
})
