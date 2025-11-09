/**
 * NCR Service
 *
 * API client for NCR CRUD operations
 */
import axios from 'axios'
import type {
  NCR,
  CreateNCRDTO,
  UpdateNCRDTO,
  NCRListResponse,
  NCRFilters,
} from '../types/ncr.types'

const API_URL = '/api/v1/ncr'

export const ncrService = {
  /**
   * Get all NCRs with optional filters
   */
  getAll: async (filters?: NCRFilters): Promise<NCRListResponse> => {
    const { data } = await axios.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get NCR by ID
   */
  getById: async (id: number): Promise<NCR> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Create new NCR
   */
  create: async (ncr: CreateNCRDTO): Promise<NCR> => {
    const { data } = await axios.post(API_URL, ncr)
    return data
  },

  /**
   * Update NCR
   */
  update: async (id: number, ncr: UpdateNCRDTO): Promise<NCR> => {
    const { data } = await axios.put(`${API_URL}/${id}`, ncr)
    return data
  },

  /**
   * Delete NCR
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },
}
