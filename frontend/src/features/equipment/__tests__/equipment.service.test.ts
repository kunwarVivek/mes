/**
 * Equipment Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { equipmentService } from '../services/equipment.service'
import type { MachineStatus } from '../services/equipment.service'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('equipmentService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listMachines', () => {
    it('should fetch all machines without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              plant_id: 1,
              machine_code: 'MCH001',
              machine_name: 'CNC Machine 1',
              machine_type: 'CNC',
              status: 'RUNNING',
              work_center_id: 1,
              capacity_per_hour: 100,
              is_active: true,
              created_at: '2024-01-01T00:00:00Z',
              updated_at: null,
            },
          ],
          total: 1,
          page: 1,
          page_size: 50,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await equipmentService.listMachines()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch machines with status filter', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 50,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await equipmentService.listMachines({ status: 'DOWN' })

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines', {
        params: { status: 'DOWN' },
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch machines with plant_id filter', async () => {
      const mockResponse = {
        data: { items: [], total: 0, page: 1, page_size: 50 },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await equipmentService.listMachines({ plant_id: 2 })

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines', {
        params: { plant_id: 2 },
      })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getMachine', () => {
    it('should fetch machine by ID', async () => {
      const mockMachine = {
        id: 1,
        plant_id: 1,
        machine_code: 'MCH001',
        machine_name: 'CNC Machine 1',
        machine_type: 'CNC',
        status: 'RUNNING' as MachineStatus,
        work_center_id: 1,
        capacity_per_hour: 100,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
      }

      mockedAxios.get.mockResolvedValue({ data: mockMachine })

      const result = await equipmentService.getMachine(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines/1')
      expect(result).toEqual(mockMachine)
    })
  })

  describe('getOEEMetrics', () => {
    it('should fetch OEE metrics for a machine', async () => {
      const mockMetrics = {
        machine_id: 1,
        machine_name: 'CNC Machine 1',
        availability: 85.5,
        performance: 92.3,
        quality: 98.1,
        oee: 77.4,
        uptime_hours: 160,
        downtime_hours: 8,
        ideal_cycle_time: 30,
        actual_cycle_time: 32,
        good_parts: 4850,
        total_parts: 5000,
        calculated_at: '2024-01-08T00:00:00Z',
      }

      mockedAxios.get.mockResolvedValue({ data: mockMetrics })

      const result = await equipmentService.getOEEMetrics(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines/1/oee', {
        params: { start_date: undefined, end_date: undefined },
      })
      expect(result).toEqual(mockMetrics)
    })

    it('should fetch OEE metrics with date range', async () => {
      const mockMetrics = {
        machine_id: 1,
        machine_name: 'CNC Machine 1',
        availability: 85.5,
        performance: 92.3,
        quality: 98.1,
        oee: 77.4,
        uptime_hours: 160,
        downtime_hours: 8,
        ideal_cycle_time: 30,
        actual_cycle_time: 32,
        good_parts: 4850,
        total_parts: 5000,
        calculated_at: '2024-01-08T00:00:00Z',
      }

      mockedAxios.get.mockResolvedValue({ data: mockMetrics })

      const result = await equipmentService.getOEEMetrics(
        1,
        '2024-01-01',
        '2024-01-07'
      )

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines/1/oee', {
        params: { start_date: '2024-01-01', end_date: '2024-01-07' },
      })
      expect(result).toEqual(mockMetrics)
    })
  })

  describe('getDowntimeHistory', () => {
    it('should fetch downtime history with default days', async () => {
      const mockDowntime = [
        {
          id: 1,
          machine_id: 1,
          start_time: '2024-01-01T08:00:00Z',
          end_time: '2024-01-01T10:00:00Z',
          duration_minutes: 120,
          category: 'BREAKDOWN',
          reason: 'Motor failure',
          notes: 'Replaced motor',
        },
      ]

      mockedAxios.get.mockResolvedValue({ data: mockDowntime })

      const result = await equipmentService.getDowntimeHistory(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines/1/downtime', {
        params: { days: 7 },
      })
      expect(result).toEqual(mockDowntime)
    })

    it('should fetch downtime history with custom days', async () => {
      const mockDowntime = []

      mockedAxios.get.mockResolvedValue({ data: mockDowntime })

      const result = await equipmentService.getDowntimeHistory(1, 30)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines/1/downtime', {
        params: { days: 30 },
      })
      expect(result).toEqual(mockDowntime)
    })
  })

  describe('updateMachineStatus', () => {
    it('should update machine status', async () => {
      const mockUpdatedMachine = {
        id: 1,
        plant_id: 1,
        machine_code: 'MCH001',
        machine_name: 'CNC Machine 1',
        machine_type: 'CNC',
        status: 'MAINTENANCE' as MachineStatus,
        work_center_id: 1,
        capacity_per_hour: 100,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-08T10:00:00Z',
      }

      mockedAxios.put.mockResolvedValue({ data: mockUpdatedMachine })

      const result = await equipmentService.updateMachineStatus(1, 'MAINTENANCE')

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/machines/1/status', {
        status: 'MAINTENANCE',
      })
      expect(result).toEqual(mockUpdatedMachine)
    })
  })
})
