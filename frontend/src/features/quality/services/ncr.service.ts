/**
 * NCR Service
 *
 * API client for NCR CRUD operations
 */
import apiClient from '@/lib/api-client'
import type { CreateNCRFormData, UpdateNCRStatusFormData, NCR } from '../schemas/ncr.schema'

export interface NCRListResponse {
  items: NCR[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface NCRListParams {
  page?: number
  page_size?: number
  status?: string
  work_order_id?: number
  search?: string
}

export const ncrService = {
  /**
   * List NCRs with optional filters and pagination
   */
  list: async (params?: NCRListParams): Promise<NCRListResponse> => {
    const { data } = await apiClient.get<NCRListResponse>('/quality/ncrs', { params })
    return data
  },

  /**
   * Get NCR by ID
   */
  get: async (id: number): Promise<NCR> => {
    const { data } = await apiClient.get<NCR>(`/quality/ncrs/${id}`)
    return data
  },

  /**
   * Create new NCR
   */
  create: async (ncr: CreateNCRFormData): Promise<NCR> => {
    const { data } = await apiClient.post<NCR>('/quality/ncrs', ncr)
    return data
  },

  /**
   * Update NCR status (workflow transitions)
   */
  updateStatus: async (id: number, statusUpdate: UpdateNCRStatusFormData): Promise<NCR> => {
    const { data } = await apiClient.patch<NCR>(`/quality/ncrs/${id}/status`, statusUpdate)
    return data
  },
}
