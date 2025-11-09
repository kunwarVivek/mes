/**
 * Production Log Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { productionLogService } from '../services/productionLog.service'
import type { ProductionLogCreateRequest } from '../types/productionLog.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('productionLogService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('logProduction', () => {
    it('should create a new production log', async () => {
      const newLog: ProductionLogCreateRequest = {
        organization_id: 1,
        plant_id: 1,
        work_order_id: 10,
        quantity_produced: 100,
        quantity_scrapped: 5,
        quantity_reworked: 2,
        operator_id: 3,
        shift_id: 1,
        notes: 'Test production run',
      }

      const mockResponse = {
        data: {
          id: 1,
          ...newLog,
          timestamp: '2025-01-15T14:30:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await productionLogService.logProduction(newLog)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/production_logs/', newLog)
      expect(result).toEqual(mockResponse.data)
    })

    it('should create log with minimal required fields', async () => {
      const minimalLog: ProductionLogCreateRequest = {
        organization_id: 1,
        plant_id: 1,
        work_order_id: 10,
        quantity_produced: 50,
      }

      const mockResponse = {
        data: {
          id: 2,
          ...minimalLog,
          quantity_scrapped: 0,
          quantity_reworked: 0,
          timestamp: '2025-01-15T15:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await productionLogService.logProduction(minimalLog)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/production_logs/', minimalLog)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('listByWorkOrder', () => {
    it('should fetch logs for a work order without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              work_order_id: 10,
              timestamp: '2025-01-15T14:30:00Z',
              quantity_produced: 100,
              quantity_scrapped: 5,
              quantity_reworked: 2,
            },
          ],
          total: 1,
          page: 1,
          page_size: 50,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await productionLogService.listByWorkOrder(10)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/production_logs/work-order/10', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch logs with time range and pagination filters', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 2,
          page_size: 20,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const filters = {
        start_time: '2025-01-01T00:00:00Z',
        end_time: '2025-01-31T23:59:59Z',
        page: 2,
        page_size: 20,
      }

      const result = await productionLogService.listByWorkOrder(10, filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/production_logs/work-order/10', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getSummary', () => {
    it('should fetch production summary for a work order', async () => {
      const mockSummary = {
        work_order_id: 10,
        total_produced: 500,
        total_scrapped: 25,
        total_reworked: 10,
        yield_rate: 93.46,
        log_count: 5,
        first_log: '2025-01-15T10:00:00Z',
        last_log: '2025-01-15T18:00:00Z',
      }

      mockedAxios.get.mockResolvedValue({ data: mockSummary })

      const result = await productionLogService.getSummary(10)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/production_logs/work-order/10/summary')
      expect(result).toEqual(mockSummary)
    })
  })

  describe('getById', () => {
    it('should fetch a single production log by ID', async () => {
      const mockLog = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        work_order_id: 10,
        timestamp: '2025-01-15T14:30:00Z',
        quantity_produced: 100,
        quantity_scrapped: 5,
        quantity_reworked: 2,
        operator_id: 3,
        shift_id: 1,
        notes: 'Test production run',
      }

      mockedAxios.get.mockResolvedValue({ data: mockLog })

      const result = await productionLogService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/production_logs/1')
      expect(result).toEqual(mockLog)
    })
  })

  describe('error handling', () => {
    it('should propagate errors from failed API calls', async () => {
      const error = new Error('Network error')
      mockedAxios.post.mockRejectedValue(error)

      await expect(
        productionLogService.logProduction({
          organization_id: 1,
          plant_id: 1,
          work_order_id: 10,
          quantity_produced: 100,
        })
      ).rejects.toThrow('Network error')
    })
  })
})
