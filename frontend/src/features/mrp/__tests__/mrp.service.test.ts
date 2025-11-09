/**
 * MRP Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { mrpService } from '../services/mrp.service'
import type { CreateMRPRunDTO, UpdateMRPRunDTO } from '../types/mrp.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('mrpService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all MRP runs without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              run_code: 'MRP001',
              run_name: 'Test MRP Run',
              run_date: '2024-01-01',
              planning_horizon_days: 30,
              status: 'DRAFT',
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

      const result = await mrpService.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/mrp-runs', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch MRP runs with filters', async () => {
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
        status: 'COMPLETED' as const,
        page: 1,
        page_size: 20,
      }

      const result = await mrpService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/mrp-runs', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getById', () => {
    it('should fetch MRP run by ID', async () => {
      const mockMRPRun = {
        id: 1,
        organization_id: 1,
        run_code: 'MRP001',
        run_name: 'Test MRP Run',
        run_date: '2024-01-01',
        planning_horizon_days: 30,
        status: 'DRAFT',
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
      }

      mockedAxios.get.mockResolvedValue({ data: mockMRPRun })

      const result = await mrpService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/mrp-runs/1')
      expect(result).toEqual(mockMRPRun)
    })
  })

  describe('create', () => {
    it('should create a new MRP run', async () => {
      const newMRPRun: CreateMRPRunDTO = {
        organization_id: 1,
        run_code: 'MRP002',
        run_name: 'New MRP Run',
        run_date: '2024-02-01',
        planning_horizon_days: 60,
        status: 'DRAFT',
        created_by_user_id: 1,
      }

      const mockResponse = {
        data: {
          ...newMRPRun,
          id: 2,
          created_at: '2024-02-01T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await mrpService.create(newMRPRun)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/mrp-runs', newMRPRun)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('update', () => {
    it('should update an existing MRP run', async () => {
      const updateData: UpdateMRPRunDTO = {
        run_name: 'Updated MRP Run',
        planning_horizon_days: 90,
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          run_code: 'MRP001',
          run_name: 'Updated MRP Run',
          run_date: '2024-01-01',
          planning_horizon_days: 90,
          status: 'DRAFT',
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      }

      mockedAxios.put.mockResolvedValue(mockResponse)

      const result = await mrpService.update(1, updateData)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/mrp-runs/1', updateData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('delete', () => {
    it('should delete an MRP run', async () => {
      mockedAxios.delete.mockResolvedValue({ data: null })

      await mrpService.delete(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/mrp-runs/1')
    })
  })

  describe('execute', () => {
    it('should execute an MRP run', async () => {
      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          run_code: 'MRP001',
          run_name: 'Test MRP Run',
          run_date: '2024-01-01',
          planning_horizon_days: 30,
          status: 'RUNNING',
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T10:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await mrpService.execute(1)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/mrp-runs/1/execute')
      expect(result).toEqual(mockResponse.data)
    })
  })
})
