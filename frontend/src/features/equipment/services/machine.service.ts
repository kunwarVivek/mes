/**
 * Machine Service
 *
 * API client for Machine CRUD operations
 */
import axios from 'axios'
import type {
  Machine,
  CreateMachineDTO,
  UpdateMachineDTO,
  MachineListResponse,
  MachineFilters,
  MachineStatusUpdateDTO,
  MachineStatusUpdateResponse,
  MachineStatusHistory,
  OEEMetrics,
} from '../types/machine.types'

const API_URL = '/api/v1/machines'

export const machineService = {
  /**
   * Get all machines with optional filters
   */
  getAll: async (filters?: MachineFilters): Promise<MachineListResponse> => {
    const { data } = await axios.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get machine by ID
   */
  getById: async (id: number): Promise<Machine> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Create new machine
   */
  create: async (machine: CreateMachineDTO): Promise<Machine> => {
    const { data } = await axios.post(API_URL, machine)
    return data
  },

  /**
   * Update existing machine
   */
  update: async (id: number, machine: UpdateMachineDTO): Promise<Machine> => {
    const { data } = await axios.put(`${API_URL}/${id}`, machine)
    return data
  },

  /**
   * Delete machine (soft delete)
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },

  /**
   * Update machine status
   */
  updateStatus: async (
    id: number,
    statusUpdate: MachineStatusUpdateDTO
  ): Promise<MachineStatusUpdateResponse> => {
    const { data } = await axios.patch(`${API_URL}/${id}/status`, statusUpdate)
    return data
  },

  /**
   * Get machine status history
   */
  getStatusHistory: async (
    id: number,
    params?: { start_date?: string; end_date?: string; limit?: number }
  ): Promise<MachineStatusHistory[]> => {
    const { data } = await axios.get(`${API_URL}/${id}/status-history`, { params })
    return data
  },

  /**
   * Get OEE metrics for a machine
   */
  getOEE: async (
    id: number,
    params: {
      start_date: string
      end_date: string
      ideal_cycle_time: number
      total_pieces: number
      defect_pieces?: number
    }
  ): Promise<OEEMetrics> => {
    const { data } = await axios.get(`${API_URL}/${id}/oee`, { params })
    return data
  },
}
