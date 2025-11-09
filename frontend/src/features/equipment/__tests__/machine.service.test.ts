/**
 * Machine Service Tests
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import { machineService } from '../services/machine.service'
import type {
  Machine,
  CreateMachineDTO,
  UpdateMachineDTO,
  MachineStatusUpdateDTO,
} from '../types/machine.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('machineService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockMachine: Machine = {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    machine_code: 'CNC001',
    machine_name: 'CNC Machine 1',
    description: 'High-precision CNC machine',
    work_center_id: 1,
    status: 'AVAILABLE',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  describe('getAll', () => {
    it('should fetch all machines without filters', async () => {
      const mockResponse = {
        items: [mockMachine],
        total: 1,
        page: 1,
        page_size: 50,
        total_pages: 1,
      }
      mockedAxios.get.mockResolvedValue({ data: mockResponse })

      const result = await machineService.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines', { params: undefined })
      expect(result).toEqual(mockResponse)
    })

    it('should fetch machines with filters', async () => {
      const filters = {
        status: 'RUNNING' as const,
        plant_id: 1,
        page: 1,
        page_size: 20,
      }
      const mockResponse = {
        items: [mockMachine],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      }
      mockedAxios.get.mockResolvedValue({ data: mockResponse })

      const result = await machineService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines', { params: filters })
      expect(result).toEqual(mockResponse)
    })

    it('should handle search filter', async () => {
      const filters = { search: 'CNC' }
      mockedAxios.get.mockResolvedValue({ data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 } })

      await machineService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines', { params: filters })
    })
  })

  describe('getById', () => {
    it('should fetch a machine by ID', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockMachine })

      const result = await machineService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines/1')
      expect(result).toEqual(mockMachine)
    })

    it('should throw error when machine not found', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Machine not found'))

      await expect(machineService.getById(999)).rejects.toThrow('Machine not found')
    })
  })

  describe('create', () => {
    it('should create a new machine', async () => {
      const newMachine: CreateMachineDTO = {
        organization_id: 1,
        plant_id: 1,
        machine_code: 'CNC002',
        machine_name: 'CNC Machine 2',
        description: 'New CNC machine',
        work_center_id: 1,
        status: 'AVAILABLE',
      }
      mockedAxios.post.mockResolvedValue({ data: { ...mockMachine, ...newMachine } })

      const result = await machineService.create(newMachine)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/machines', newMachine)
      expect(result.machine_code).toBe(newMachine.machine_code)
    })

    it('should handle validation errors', async () => {
      const invalidMachine = {
        machine_code: '',
      } as CreateMachineDTO

      mockedAxios.post.mockRejectedValue(new Error('Validation error'))

      await expect(machineService.create(invalidMachine)).rejects.toThrow('Validation error')
    })
  })

  describe('update', () => {
    it('should update a machine', async () => {
      const updates: UpdateMachineDTO = {
        machine_name: 'Updated CNC Machine',
        description: 'Updated description',
      }
      const updatedMachine = { ...mockMachine, ...updates }
      mockedAxios.put.mockResolvedValue({ data: updatedMachine })

      const result = await machineService.update(1, updates)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/machines/1', updates)
      expect(result.machine_name).toBe(updates.machine_name)
    })

    it('should allow partial updates', async () => {
      const updates: UpdateMachineDTO = { is_active: false }
      mockedAxios.put.mockResolvedValue({ data: { ...mockMachine, is_active: false } })

      const result = await machineService.update(1, updates)

      expect(result.is_active).toBe(false)
    })
  })

  describe('delete', () => {
    it('should delete a machine', async () => {
      mockedAxios.delete.mockResolvedValue({ data: null })

      await machineService.delete(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/machines/1')
    })

    it('should handle delete errors', async () => {
      mockedAxios.delete.mockRejectedValue(new Error('Cannot delete machine'))

      await expect(machineService.delete(1)).rejects.toThrow('Cannot delete machine')
    })
  })

  describe('updateStatus', () => {
    it('should update machine status', async () => {
      const statusUpdate: MachineStatusUpdateDTO = {
        status: 'RUNNING',
        notes: 'Production started',
      }
      const mockResponse = {
        machine: { ...mockMachine, status: 'RUNNING' },
        status_history: {
          id: 1,
          machine_id: 1,
          status: 'RUNNING',
          started_at: '2024-01-01T10:00:00Z',
          notes: 'Production started',
        },
      }
      mockedAxios.patch.mockResolvedValue({ data: mockResponse })

      const result = await machineService.updateStatus(1, statusUpdate)

      expect(mockedAxios.patch).toHaveBeenCalledWith('/api/v1/machines/1/status', statusUpdate)
      expect(result.machine.status).toBe('RUNNING')
      expect(result.status_history.notes).toBe('Production started')
    })

    it('should update status without notes', async () => {
      const statusUpdate: MachineStatusUpdateDTO = { status: 'MAINTENANCE' }
      const mockResponse = {
        machine: { ...mockMachine, status: 'MAINTENANCE' },
        status_history: {
          id: 2,
          machine_id: 1,
          status: 'MAINTENANCE',
          started_at: '2024-01-01T11:00:00Z',
        },
      }
      mockedAxios.patch.mockResolvedValue({ data: mockResponse })

      const result = await machineService.updateStatus(1, statusUpdate)

      expect(result.machine.status).toBe('MAINTENANCE')
    })
  })

  describe('getStatusHistory', () => {
    it('should fetch status history without filters', async () => {
      const mockHistory = [
        {
          id: 1,
          machine_id: 1,
          status: 'RUNNING' as const,
          started_at: '2024-01-01T10:00:00Z',
          ended_at: '2024-01-01T12:00:00Z',
          duration_minutes: 120,
        },
      ]
      mockedAxios.get.mockResolvedValue({ data: mockHistory })

      const result = await machineService.getStatusHistory(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines/1/status-history', { params: undefined })
      expect(result).toEqual(mockHistory)
    })

    it('should fetch status history with date filters', async () => {
      const params = {
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        limit: 50,
      }
      mockedAxios.get.mockResolvedValue({ data: [] })

      await machineService.getStatusHistory(1, params)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines/1/status-history', { params })
    })
  })

  describe('getOEE', () => {
    it('should fetch OEE metrics', async () => {
      const params = {
        start_date: '2024-01-01T00:00:00Z',
        end_date: '2024-01-01T08:00:00Z',
        ideal_cycle_time: 0.5,
        total_pieces: 900,
        defect_pieces: 10,
      }
      const mockOEE = {
        availability: 0.95,
        performance: 0.93,
        quality: 0.99,
        oee_score: 0.87,
      }
      mockedAxios.get.mockResolvedValue({ data: mockOEE })

      const result = await machineService.getOEE(1, params)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/machines/1/oee', { params })
      expect(result).toEqual(mockOEE)
      expect(result.oee_score).toBeCloseTo(0.87, 2)
    })

    it('should handle OEE with zero defects', async () => {
      const params = {
        start_date: '2024-01-01T00:00:00Z',
        end_date: '2024-01-01T08:00:00Z',
        ideal_cycle_time: 0.5,
        total_pieces: 900,
        defect_pieces: 0,
      }
      const mockOEE = {
        availability: 0.95,
        performance: 0.93,
        quality: 1.0,
        oee_score: 0.88,
      }
      mockedAxios.get.mockResolvedValue({ data: mockOEE })

      const result = await machineService.getOEE(1, params)

      expect(result.quality).toBe(1.0)
    })
  })
})
