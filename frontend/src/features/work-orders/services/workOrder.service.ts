/**
 * Work Order Service
 *
 * API client for Work Order CRUD operations and state transitions
 */
import axios from 'axios'
import type {
  WorkOrder,
  CreateWorkOrderDTO,
  UpdateWorkOrderDTO,
  WorkOrderListResponse,
  WorkOrderFilters,
} from '../types/workOrder.types'

const API_URL = '/api/v1/work-orders'

export const workOrderService = {
  /**
   * Get all work orders with optional filters
   */
  getAll: async (filters?: WorkOrderFilters): Promise<WorkOrderListResponse> => {
    const { data } = await axios.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get work order by ID
   */
  getById: async (id: number): Promise<WorkOrder> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Create new work order
   */
  create: async (workOrder: CreateWorkOrderDTO): Promise<WorkOrder> => {
    const { data } = await axios.post(API_URL, workOrder)
    return data
  },

  /**
   * Update existing work order
   */
  update: async (id: number, workOrder: UpdateWorkOrderDTO): Promise<WorkOrder> => {
    const { data } = await axios.put(`${API_URL}/${id}`, workOrder)
    return data
  },

  /**
   * Cancel work order (soft delete)
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },

  /**
   * Release work order for production (PLANNED -> RELEASED)
   */
  release: async (id: number): Promise<WorkOrder> => {
    const { data } = await axios.post(`${API_URL}/${id}/release`)
    return data
  },

  /**
   * Start production (RELEASED -> IN_PROGRESS)
   */
  start: async (id: number): Promise<WorkOrder> => {
    const { data } = await axios.post(`${API_URL}/${id}/start`)
    return data
  },

  /**
   * Complete work order (IN_PROGRESS -> COMPLETED)
   */
  complete: async (id: number): Promise<WorkOrder> => {
    const { data } = await axios.post(`${API_URL}/${id}/complete`)
    return data
  },
}
