/**
 * MRP Service
 *
 * API client for MRP CRUD operations
 */
import axios from 'axios'
import type {
  MRPRun,
  CreateMRPRunDTO,
  UpdateMRPRunDTO,
  MRPRunListResponse,
  MRPRunFilters,
} from '../types/mrp.types'

const API_URL = '/api/v1/mrp-runs'

export const mrpService = {
  /**
   * Get all MRP runs with optional filters
   */
  getAll: async (filters?: MRPRunFilters): Promise<MRPRunListResponse> => {
    const { data } = await axios.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get MRP run by ID
   */
  getById: async (id: number): Promise<MRPRun> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Create new MRP run
   */
  create: async (mrpRun: CreateMRPRunDTO): Promise<MRPRun> => {
    const { data } = await axios.post(API_URL, mrpRun)
    return data
  },

  /**
   * Update existing MRP run
   */
  update: async (id: number, mrpRun: UpdateMRPRunDTO): Promise<MRPRun> => {
    const { data } = await axios.put(`${API_URL}/${id}`, mrpRun)
    return data
  },

  /**
   * Delete MRP run
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },

  /**
   * Execute MRP run
   */
  execute: async (id: number): Promise<MRPRun> => {
    const { data } = await axios.post(`${API_URL}/${id}/execute`)
    return data
  },
}
