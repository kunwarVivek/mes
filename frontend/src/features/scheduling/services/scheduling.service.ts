/**
 * Scheduling Service
 *
 * API client for Scheduled Operation CRUD operations
 */
import axios from 'axios'
import type {
  ScheduledOperation,
  CreateScheduledOperationDTO,
  UpdateScheduledOperationDTO,
  ScheduledOperationListResponse,
  ScheduledOperationFilters,
} from '../types/scheduling.types'

const API_URL = '/api/v1/scheduled-operations'

export const schedulingService = {
  /**
   * Get all scheduled operations with optional filters
   */
  getAll: async (
    filters?: ScheduledOperationFilters
  ): Promise<ScheduledOperationListResponse> => {
    const { data } = await axios.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get scheduled operation by ID
   */
  getById: async (id: number): Promise<ScheduledOperation> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Create new scheduled operation
   */
  create: async (operation: CreateScheduledOperationDTO): Promise<ScheduledOperation> => {
    const { data } = await axios.post(API_URL, operation)
    return data
  },

  /**
   * Update existing scheduled operation
   */
  update: async (
    id: number,
    operation: UpdateScheduledOperationDTO
  ): Promise<ScheduledOperation> => {
    const { data } = await axios.put(`${API_URL}/${id}`, operation)
    return data
  },

  /**
   * Delete scheduled operation
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },

  /**
   * Get operations by work order
   */
  getByWorkOrder: async (workOrderId: number): Promise<ScheduledOperation[]> => {
    const { data } = await axios.get(`${API_URL}/work-order/${workOrderId}`)
    return data
  },
}
