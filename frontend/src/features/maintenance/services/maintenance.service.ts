/**
 * Maintenance Service
 *
 * API client for Maintenance CRUD operations
 */
import axios from 'axios'
import type {
  PMSchedule,
  CreatePMScheduleDTO,
  UpdatePMScheduleDTO,
  PMScheduleFilters,
  DowntimeEvent,
  CreateDowntimeEventDTO,
  UpdateDowntimeEventDTO,
  DowntimeEventFilters,
  MTBFMTTRMetrics,
} from '../types/maintenance.types'

const PM_SCHEDULES_URL = '/api/v1/maintenance/pm-schedules'
const DOWNTIME_EVENTS_URL = '/api/v1/maintenance/downtime-events'
const METRICS_URL = '/api/v1/maintenance/metrics/mtbf-mttr'

export const maintenanceService = {
  /**
   * Get all PM schedules with optional filters
   */
  getAll: async (filters?: PMScheduleFilters): Promise<PMSchedule[]> => {
    const { data } = await axios.get(PM_SCHEDULES_URL, { params: filters })
    return data
  },

  /**
   * Get PM schedule by ID
   */
  getById: async (id: number): Promise<PMSchedule> => {
    const { data } = await axios.get(`${PM_SCHEDULES_URL}/${id}`)
    return data
  },

  /**
   * Create new PM schedule
   */
  create: async (schedule: CreatePMScheduleDTO): Promise<PMSchedule> => {
    const { data } = await axios.post(PM_SCHEDULES_URL, schedule)
    return data
  },

  /**
   * Update existing PM schedule
   */
  update: async (id: number, schedule: UpdatePMScheduleDTO): Promise<PMSchedule> => {
    const { data } = await axios.patch(`${PM_SCHEDULES_URL}/${id}`, schedule)
    return data
  },

  /**
   * Delete PM schedule
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${PM_SCHEDULES_URL}/${id}`)
  },

  /**
   * Get downtime events with optional filters
   */
  getDowntimeEvents: async (filters?: DowntimeEventFilters): Promise<DowntimeEvent[]> => {
    const { data } = await axios.get(DOWNTIME_EVENTS_URL, { params: filters || {} })
    return data
  },

  /**
   * Create new downtime event
   */
  createDowntimeEvent: async (event: CreateDowntimeEventDTO): Promise<DowntimeEvent> => {
    const { data } = await axios.post(DOWNTIME_EVENTS_URL, event)
    return data
  },

  /**
   * Update downtime event (typically to end it)
   */
  updateDowntimeEvent: async (
    id: number,
    event: UpdateDowntimeEventDTO
  ): Promise<DowntimeEvent> => {
    const { data } = await axios.patch(`${DOWNTIME_EVENTS_URL}/${id}`, event)
    return data
  },

  /**
   * Get MTBF/MTTR metrics for a machine
   */
  getMTBFMTTRMetrics: async (
    machine_id: number,
    start_date: string,
    end_date: string
  ): Promise<MTBFMTTRMetrics> => {
    const { data } = await axios.get(METRICS_URL, {
      params: { machine_id, start_date, end_date },
    })
    return data
  },
}
