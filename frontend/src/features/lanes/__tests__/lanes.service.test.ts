/**
 * Lanes Service Tests
 *
 * TDD RED Phase: Test service API methods
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { lanesService } from '../services/lanes.service'
import type { Lane, LaneAssignment, LaneCapacity } from '../types/lane.types'

// Mock axios
vi.mock('axios')
const mockedAxios = vi.mocked(axios)

describe('Lanes Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listLanes', () => {
    it('should fetch lanes with filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              plant_id: 100,
              lane_code: 'L001',
              lane_name: 'Assembly Line 1',
              capacity_per_day: 1000,
              is_active: true,
              created_at: '2025-01-01T00:00:00Z',
            },
          ] as Lane[],
          total: 1,
          page: 1,
          page_size: 10,
        },
      }

      mockedAxios.get.mockResolvedValueOnce(mockResponse)

      const result = await lanesService.listLanes({ plant_id: 100, is_active: true })

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/lanes', {
        params: { plant_id: 100, is_active: true },
      })
      expect(result.items).toHaveLength(1)
      expect(result.items[0].lane_code).toBe('L001')
    })

    it('should fetch lanes without filters', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
        },
      }

      mockedAxios.get.mockResolvedValueOnce(mockResponse)

      await lanesService.listLanes()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/lanes', { params: undefined })
    })
  })

  describe('getLane', () => {
    it('should fetch single lane by id', async () => {
      const mockLane: Lane = {
        id: 1,
        plant_id: 100,
        lane_code: 'L001',
        lane_name: 'Assembly Line 1',
        capacity_per_day: 1000,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      }

      mockedAxios.get.mockResolvedValueOnce({ data: mockLane })

      const result = await lanesService.getLane(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/lanes/1')
      expect(result.id).toBe(1)
      expect(result.lane_code).toBe('L001')
    })
  })

  describe('getLaneCapacity', () => {
    it('should fetch capacity for lane and date', async () => {
      const mockCapacity: LaneCapacity = {
        lane_id: 1,
        date: '2025-01-15',
        total_capacity: 1000,
        allocated_capacity: 800,
        available_capacity: 200,
        utilization_rate: 80,
        assignment_count: 3,
      }

      mockedAxios.get.mockResolvedValueOnce({ data: mockCapacity })

      const result = await lanesService.getLaneCapacity(1, '2025-01-15')

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/lanes/1/capacity', {
        params: { date: '2025-01-15' },
      })
      expect(result.utilization_rate).toBe(80)
      expect(result.available_capacity).toBe(200)
    })
  })

  describe('listAssignments', () => {
    it('should fetch assignments with filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 100,
              lane_id: 1,
              work_order_id: 500,
              scheduled_start: '2025-01-15',
              scheduled_end: '2025-01-20',
              allocated_capacity: 500,
              priority: 1,
              status: 'PLANNED',
              created_at: '2025-01-01T00:00:00Z',
            },
          ] as LaneAssignment[],
          total: 1,
          page: 1,
          page_size: 10,
        },
      }

      mockedAxios.get.mockResolvedValueOnce(mockResponse)

      const result = await lanesService.listAssignments({
        lane_id: 1,
        start_date: '2025-01-15',
        end_date: '2025-01-20',
      })

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/lanes/assignments', {
        params: { lane_id: 1, start_date: '2025-01-15', end_date: '2025-01-20' },
      })
      expect(result.items).toHaveLength(1)
    })
  })

  describe('getAssignment', () => {
    it('should fetch single assignment by id', async () => {
      const mockAssignment: LaneAssignment = {
        id: 1,
        organization_id: 1,
        plant_id: 100,
        lane_id: 1,
        work_order_id: 500,
        scheduled_start: '2025-01-15',
        scheduled_end: '2025-01-20',
        allocated_capacity: 500,
        priority: 1,
        status: 'PLANNED',
        created_at: '2025-01-01T00:00:00Z',
      }

      mockedAxios.get.mockResolvedValueOnce({ data: mockAssignment })

      const result = await lanesService.getAssignment(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/lanes/assignments/1')
      expect(result.id).toBe(1)
      expect(result.work_order_id).toBe(500)
    })
  })

  describe('createAssignment', () => {
    it('should create new assignment', async () => {
      const createRequest = {
        organization_id: 1,
        plant_id: 100,
        lane_id: 1,
        work_order_id: 500,
        scheduled_start: '2025-01-15',
        scheduled_end: '2025-01-20',
        allocated_capacity: 500,
        priority: 1,
      }

      const mockResponse: LaneAssignment = {
        id: 1,
        ...createRequest,
        status: 'PLANNED',
        created_at: '2025-01-01T00:00:00Z',
      }

      mockedAxios.post.mockResolvedValueOnce({ data: mockResponse })

      const result = await lanesService.createAssignment(createRequest)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/lanes/assignments', createRequest)
      expect(result.id).toBe(1)
      expect(result.status).toBe('PLANNED')
    })
  })

  describe('updateAssignment', () => {
    it('should update existing assignment', async () => {
      const updateRequest = {
        allocated_capacity: 600,
        status: 'ACTIVE' as const,
      }

      const mockResponse: LaneAssignment = {
        id: 1,
        organization_id: 1,
        plant_id: 100,
        lane_id: 1,
        work_order_id: 500,
        scheduled_start: '2025-01-15',
        scheduled_end: '2025-01-20',
        allocated_capacity: 600,
        priority: 1,
        status: 'ACTIVE',
        created_at: '2025-01-01T00:00:00Z',
      }

      mockedAxios.put.mockResolvedValueOnce({ data: mockResponse })

      const result = await lanesService.updateAssignment(1, updateRequest)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/lanes/assignments/1', updateRequest)
      expect(result.allocated_capacity).toBe(600)
      expect(result.status).toBe('ACTIVE')
    })
  })

  describe('deleteAssignment', () => {
    it('should delete assignment', async () => {
      mockedAxios.delete.mockResolvedValueOnce({ data: null })

      await lanesService.deleteAssignment(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/lanes/assignments/1')
    })
  })
})
