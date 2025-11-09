/**
 * Maintenance Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { maintenanceService } from '../services/maintenance.service'
import type {
  CreatePMScheduleDTO,
  UpdatePMScheduleDTO,
  CreateDowntimeEventDTO,
  UpdateDowntimeEventDTO,
} from '../types/maintenance.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('maintenanceService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('PM Schedules', () => {
    describe('getAll', () => {
      it('should fetch all PM schedules without filters', async () => {
        const mockResponse = {
          data: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              schedule_code: 'PM001',
              schedule_name: 'Monthly Lubrication',
              machine_id: 10,
              trigger_type: 'CALENDAR',
              frequency_days: 30,
              meter_threshold: null,
              is_active: true,
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-01T00:00:00Z',
            },
          ],
        }

        mockedAxios.get.mockResolvedValue(mockResponse)

        const result = await maintenanceService.getAll()

        expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/maintenance/pm-schedules', {
          params: undefined,
        })
        expect(result).toEqual(mockResponse.data)
      })

      it('should fetch PM schedules with filters', async () => {
        const mockResponse = { data: [] }

        mockedAxios.get.mockResolvedValue(mockResponse)

        const filters = {
          machine_id: 10,
          is_active: true,
        }

        const result = await maintenanceService.getAll(filters)

        expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/maintenance/pm-schedules', {
          params: filters,
        })
        expect(result).toEqual(mockResponse.data)
      })
    })

    describe('getById', () => {
      it('should fetch PM schedule by ID', async () => {
        const mockSchedule = {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          schedule_code: 'PM001',
          schedule_name: 'Monthly Lubrication',
          machine_id: 10,
          trigger_type: 'CALENDAR',
          frequency_days: 30,
          meter_threshold: null,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        }

        mockedAxios.get.mockResolvedValue({ data: mockSchedule })

        const result = await maintenanceService.getById(1)

        expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/maintenance/pm-schedules/1')
        expect(result).toEqual(mockSchedule)
      })
    })

    describe('create', () => {
      it('should create a new PM schedule', async () => {
        const newSchedule: CreatePMScheduleDTO = {
          schedule_code: 'PM002',
          schedule_name: 'Quarterly Inspection',
          machine_id: 10,
          trigger_type: 'CALENDAR',
          frequency_days: 90,
          is_active: true,
        }

        const mockResponse = {
          data: {
            ...newSchedule,
            id: 2,
            organization_id: 1,
            plant_id: 1,
            meter_threshold: null,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        }

        mockedAxios.post.mockResolvedValue(mockResponse)

        const result = await maintenanceService.create(newSchedule)

        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/v1/maintenance/pm-schedules',
          newSchedule
        )
        expect(result).toEqual(mockResponse.data)
      })
    })

    describe('update', () => {
      it('should update an existing PM schedule', async () => {
        const updateData: UpdatePMScheduleDTO = {
          schedule_name: 'Updated Schedule',
          frequency_days: 45,
        }

        const mockResponse = {
          data: {
            id: 1,
            organization_id: 1,
            plant_id: 1,
            schedule_code: 'PM001',
            schedule_name: 'Updated Schedule',
            machine_id: 10,
            trigger_type: 'CALENDAR',
            frequency_days: 45,
            meter_threshold: null,
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-02T00:00:00Z',
          },
        }

        mockedAxios.patch.mockResolvedValue(mockResponse)

        const result = await maintenanceService.update(1, updateData)

        expect(mockedAxios.patch).toHaveBeenCalledWith(
          '/api/v1/maintenance/pm-schedules/1',
          updateData
        )
        expect(result).toEqual(mockResponse.data)
      })
    })

    describe('delete', () => {
      it('should delete a PM schedule', async () => {
        mockedAxios.delete.mockResolvedValue({ data: null })

        await maintenanceService.delete(1)

        expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/maintenance/pm-schedules/1')
      })
    })
  })

  describe('Downtime Events', () => {
    describe('getDowntimeEvents', () => {
      it('should fetch all downtime events without filters', async () => {
        const mockResponse = {
          data: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              machine_id: 10,
              category: 'BREAKDOWN',
              reason: 'Belt failure',
              started_at: '2024-01-01T08:00:00Z',
              ended_at: '2024-01-01T10:30:00Z',
              duration_minutes: 150,
              notes: 'Replaced belt',
              created_at: '2024-01-01T08:00:00Z',
            },
          ],
        }

        mockedAxios.get.mockResolvedValue(mockResponse)

        const result = await maintenanceService.getDowntimeEvents()

        expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/maintenance/downtime-events', {
          params: {},
        })
        expect(result).toEqual(mockResponse.data)
      })

      it('should fetch downtime events with filters', async () => {
        const mockResponse = { data: [] }

        mockedAxios.get.mockResolvedValue(mockResponse)

        const result = await maintenanceService.getDowntimeEvents({
          machine_id: 10,
          category: 'BREAKDOWN',
          start_date: '2024-01-01',
          end_date: '2024-01-31',
        })

        expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/maintenance/downtime-events', {
          params: {
            machine_id: 10,
            category: 'BREAKDOWN',
            start_date: '2024-01-01',
            end_date: '2024-01-31',
          },
        })
        expect(result).toEqual(mockResponse.data)
      })
    })

    describe('createDowntimeEvent', () => {
      it('should create a new downtime event', async () => {
        const newEvent: CreateDowntimeEventDTO = {
          machine_id: 10,
          category: 'BREAKDOWN',
          reason: 'Motor overheating',
          started_at: '2024-01-02T14:00:00Z',
        }

        const mockResponse = {
          data: {
            ...newEvent,
            id: 2,
            organization_id: 1,
            plant_id: 1,
            ended_at: null,
            duration_minutes: null,
            notes: null,
            created_at: '2024-01-02T14:00:00Z',
          },
        }

        mockedAxios.post.mockResolvedValue(mockResponse)

        const result = await maintenanceService.createDowntimeEvent(newEvent)

        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/v1/maintenance/downtime-events',
          newEvent
        )
        expect(result).toEqual(mockResponse.data)
      })
    })

    describe('updateDowntimeEvent', () => {
      it('should update a downtime event to end it', async () => {
        const updateData: UpdateDowntimeEventDTO = {
          ended_at: '2024-01-02T16:00:00Z',
          notes: 'Replaced motor',
        }

        const mockResponse = {
          data: {
            id: 2,
            organization_id: 1,
            plant_id: 1,
            machine_id: 10,
            category: 'BREAKDOWN',
            reason: 'Motor overheating',
            started_at: '2024-01-02T14:00:00Z',
            ended_at: '2024-01-02T16:00:00Z',
            duration_minutes: 120,
            notes: 'Replaced motor',
            created_at: '2024-01-02T14:00:00Z',
          },
        }

        mockedAxios.patch.mockResolvedValue(mockResponse)

        const result = await maintenanceService.updateDowntimeEvent(2, updateData)

        expect(mockedAxios.patch).toHaveBeenCalledWith(
          '/api/v1/maintenance/downtime-events/2',
          updateData
        )
        expect(result).toEqual(mockResponse.data)
      })
    })
  })

  describe('MTBF/MTTR Metrics', () => {
    describe('getMTBFMTTRMetrics', () => {
      it('should fetch MTBF/MTTR metrics for a machine', async () => {
        const mockResponse = {
          data: {
            machine_id: 10,
            time_period_start: '2024-01-01T00:00:00Z',
            time_period_end: '2024-01-31T23:59:59Z',
            total_operating_time: 42000,
            total_repair_time: 720,
            number_of_failures: 3,
            mtbf: 14000,
            mttr: 240,
            availability: 0.983,
          },
        }

        mockedAxios.get.mockResolvedValue(mockResponse)

        const result = await maintenanceService.getMTBFMTTRMetrics(
          10,
          '2024-01-01T00:00:00Z',
          '2024-01-31T23:59:59Z'
        )

        expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/maintenance/metrics/mtbf-mttr', {
          params: {
            machine_id: 10,
            start_date: '2024-01-01T00:00:00Z',
            end_date: '2024-01-31T23:59:59Z',
          },
        })
        expect(result).toEqual(mockResponse.data)
      })
    })
  })
})
