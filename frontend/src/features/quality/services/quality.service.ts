/**
 * Quality Service
 *
 * API client for NCR CRUD operations
 */
import axios from 'axios'
import type {
  NCR,
  CreateNCRDTO,
  UpdateNCRStatusDTO,
  NCRListResponse,
  NCRFilters,
} from '../types/quality.types'

const API_URL = '/api/v1/quality/ncrs'

export const qualityService = {
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
   * Update NCR status
   */
  updateStatus: async (id: number, statusUpdate: UpdateNCRStatusDTO): Promise<NCR> => {
    const { data } = await axios.patch(`${API_URL}/${id}/status`, statusUpdate)
    return data
  },

  /**
   * Delete NCR (soft delete)
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },

  /**
   * Review NCR (OPEN → IN_REVIEW)
   */
  review: async (id: number): Promise<NCR> => {
    const { data } = await axios.patch(`${API_URL}/${id}/status`, {
      status: 'IN_REVIEW',
    })
    return data
  },

  /**
   * Resolve NCR (IN_REVIEW → RESOLVED)
   */
  resolve: async (id: number, resolution_notes: string, resolved_by_user_id: number): Promise<NCR> => {
    const { data } = await axios.patch(`${API_URL}/${id}/status`, {
      status: 'RESOLVED',
      resolution_notes,
      resolved_by_user_id,
    })
    return data
  },
}
