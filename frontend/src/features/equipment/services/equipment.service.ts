/**
 * Equipment Service
 *
 * API client for Equipment/Machine operations and OEE metrics
 */
import axios from 'axios'

export type MachineStatus = 'AVAILABLE' | 'RUNNING' | 'IDLE' | 'DOWN' | 'MAINTENANCE'

export interface Machine {
  id: number
  plant_id: number
  machine_code: string
  machine_name: string
  machine_type: string
  status: MachineStatus
  work_center_id: number | null
  capacity_per_hour: number
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface OEEMetrics {
  machine_id: number
  machine_name: string
  availability: number  // Percentage
  performance: number   // Percentage
  quality: number       // Percentage
  oee: number          // Percentage
  uptime_hours: number
  downtime_hours: number
  ideal_cycle_time: number
  actual_cycle_time: number
  good_parts: number
  total_parts: number
  calculated_at: string
}

export interface DowntimeEvent {
  id: number
  machine_id: number
  start_time: string
  end_time: string | null
  duration_minutes: number | null
  category: string
  reason: string
  notes: string | null
}

const API_URL = '/api/v1/machines'

export const equipmentService = {
  listMachines: async (params?: { plant_id?: number; status?: MachineStatus }) => {
    const { data } = await axios.get(API_URL, { params })
    return data
  },

  getMachine: async (id: number): Promise<Machine> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  getOEEMetrics: async (machineId: number, startDate?: string, endDate?: string): Promise<OEEMetrics> => {
    const { data } = await axios.get(`${API_URL}/${machineId}/oee`, {
      params: { start_date: startDate, end_date: endDate }
    })
    return data
  },

  getDowntimeHistory: async (machineId: number, days: number = 7) => {
    const { data } = await axios.get(`${API_URL}/${machineId}/downtime`, {
      params: { days }
    })
    return data
  },

  updateMachineStatus: async (id: number, status: MachineStatus): Promise<Machine> => {
    const { data } = await axios.put(`${API_URL}/${id}/status`, { status })
    return data
  }
}
