/**
 * Shift Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { shiftService } from '../services/shift.service'
import type { CreateShiftDTO, UpdateShiftDTO, CreateShiftHandoverDTO } from '../types/shift.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('shiftService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all shifts without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              shift_code: 'A',
              shift_name: 'Morning Shift',
              start_time: '06:00:00',
              end_time: '14:00:00',
              production_target: 1000,
              is_active: true,
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

      const result = await shiftService.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/shifts', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch shifts with filters', async () => {
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
        is_active: true,
        shift_code: 'A',
        page: 1,
        page_size: 20,
      }

      const result = await shiftService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/shifts', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getById', () => {
    it('should fetch shift by ID', async () => {
      const mockShift = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        shift_code: 'A',
        shift_name: 'Morning Shift',
        start_time: '06:00:00',
        end_time: '14:00:00',
        production_target: 1000,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }

      mockedAxios.get.mockResolvedValue({ data: mockShift })

      const result = await shiftService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/shifts/1')
      expect(result).toEqual(mockShift)
    })
  })

  describe('create', () => {
    it('should create a new shift', async () => {
      const newShift: CreateShiftDTO = {
        shift_name: 'Night Shift',
        shift_code: 'C',
        start_time: '22:00:00',
        end_time: '06:00:00',
        production_target: 800,
        is_active: true,
      }

      const mockResponse = {
        data: {
          ...newShift,
          id: 2,
          organization_id: 1,
          plant_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await shiftService.create(newShift)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/shifts', newShift)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('update', () => {
    it('should update an existing shift', async () => {
      const updateData: UpdateShiftDTO = {
        shift_name: 'Updated Morning Shift',
        production_target: 1200,
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          shift_code: 'A',
          shift_name: 'Updated Morning Shift',
          start_time: '06:00:00',
          end_time: '14:00:00',
          production_target: 1200,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      }

      mockedAxios.put.mockResolvedValue(mockResponse)

      const result = await shiftService.update(1, updateData)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/shifts/1', updateData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('createHandover', () => {
    it('should create a shift handover', async () => {
      const handoverData: CreateShiftHandoverDTO = {
        from_shift_id: 1,
        to_shift_id: 2,
        handover_date: '2024-01-01T14:00:00Z',
        wip_quantity: 50,
        production_summary: 'Completed 950 units, 50 in progress',
        quality_issues: 'None',
        machine_status: 'All operational',
        material_status: 'Sufficient stock',
      }

      const mockResponse = {
        data: {
          ...handoverData,
          id: 1,
          organization_id: 1,
          plant_id: 1,
          handover_by_user_id: 1,
          created_at: '2024-01-01T14:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await shiftService.createHandover(handoverData)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/shifts/handovers', handoverData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getHandovers', () => {
    it('should fetch all handovers without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              from_shift_id: 1,
              to_shift_id: 2,
              handover_date: '2024-01-01T14:00:00Z',
              wip_quantity: 50,
              production_summary: 'Completed 950 units',
              handover_by_user_id: 1,
              created_at: '2024-01-01T14:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 50,
          total_pages: 1,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await shiftService.getHandovers()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/shifts/handovers', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch handovers with filters', async () => {
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
        from_shift_id: 1,
        acknowledged: false,
        page: 1,
        page_size: 20,
      }

      const result = await shiftService.getHandovers(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/shifts/handovers', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('acknowledgeHandover', () => {
    it('should acknowledge a shift handover', async () => {
      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          from_shift_id: 1,
          to_shift_id: 2,
          handover_date: '2024-01-01T14:00:00Z',
          wip_quantity: 50,
          production_summary: 'Completed 950 units',
          handover_by_user_id: 1,
          acknowledged_by_user_id: 2,
          acknowledged_at: '2024-01-01T14:05:00Z',
          created_at: '2024-01-01T14:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await shiftService.acknowledgeHandover(1)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/shifts/handovers/1/acknowledge', {})
      expect(result).toEqual(mockResponse.data)
    })
  })
})
