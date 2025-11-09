/**
 * Production Log Service
 *
 * API client for Production Log CRUD operations
 */
import axios from 'axios'
import type {
  ProductionLog,
  ProductionLogCreateRequest,
  ProductionLogListResponse,
  ProductionSummary,
  ProductionLogFilters,
} from '../types/productionLog.types'

const API_URL = '/api/v1/production_logs'

export const productionLogService = {
  /**
   * Create a new production log entry
   */
  logProduction: async (data: ProductionLogCreateRequest): Promise<ProductionLog> => {
    const { data: response } = await axios.post(`${API_URL}/`, data)
    return response
  },

  /**
   * Get production logs by work order with optional filters
   */
  listByWorkOrder: async (
    workOrderId: number,
    params?: ProductionLogFilters
  ): Promise<ProductionLogListResponse> => {
    const { data } = await axios.get(`${API_URL}/work-order/${workOrderId}`, { params })
    return data
  },

  /**
   * Get production summary statistics for a work order
   */
  getSummary: async (workOrderId: number): Promise<ProductionSummary> => {
    const { data } = await axios.get(`${API_URL}/work-order/${workOrderId}/summary`)
    return data
  },

  /**
   * Get single production log by ID
   */
  getById: async (logId: number): Promise<ProductionLog> => {
    const { data } = await axios.get(`${API_URL}/${logId}`)
    return data
  },
}
