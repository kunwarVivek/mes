/**
 * Work Order Service
 *
 * API client for Work Order CRUD operations and state transitions
 */
import apiClient from '@/lib/api-client'
import type {
  CreateWorkOrderFormData,
  UpdateWorkOrderFormData,
  WorkOrder,
} from '../schemas/work-order.schema'

export interface WorkOrderListResponse {
  items: WorkOrder[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface WorkOrderListParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  material_id?: number
  priority?: number
  order_type?: string
}

export interface AddOperationRequest {
  operation_sequence: number
  operation_name: string
  setup_time_minutes?: number
  run_time_minutes?: number
}

export interface AddMaterialRequest {
  material_id: number
  required_quantity: number
}

export const workOrderService = {
  /**
   * List work orders with optional filters and pagination
   */
  list: async (params?: WorkOrderListParams): Promise<WorkOrderListResponse> => {
    const { data } = await apiClient.get<WorkOrderListResponse>('/work-orders', { params })
    return data
  },

  /**
   * Get work order by ID
   */
  get: async (id: number): Promise<WorkOrder> => {
    const { data } = await apiClient.get<WorkOrder>(`/work-orders/${id}`)
    return data
  },

  /**
   * Create new work order
   */
  create: async (workOrder: CreateWorkOrderFormData): Promise<WorkOrder> => {
    const { data } = await apiClient.post<WorkOrder>('/work-orders', workOrder)
    return data
  },

  /**
   * Update existing work order
   */
  update: async (id: number, workOrder: UpdateWorkOrderFormData): Promise<WorkOrder> => {
    const { data } = await apiClient.put<WorkOrder>(`/work-orders/${id}`, workOrder)
    return data
  },

  /**
   * Cancel work order
   */
  cancel: async (id: number): Promise<WorkOrder> => {
    const { data } = await apiClient.delete<WorkOrder>(`/work-orders/${id}`)
    return data
  },

  /**
   * State transition: PLANNED -> RELEASED
   */
  release: async (id: number): Promise<WorkOrder> => {
    const { data } = await apiClient.post<WorkOrder>(`/work-orders/${id}/release`, {})
    return data
  },

  /**
   * State transition: RELEASED -> IN_PROGRESS
   */
  start: async (id: number): Promise<WorkOrder> => {
    const { data } = await apiClient.post<WorkOrder>(`/work-orders/${id}/start`, {})
    return data
  },

  /**
   * State transition: IN_PROGRESS -> COMPLETED
   */
  complete: async (id: number): Promise<WorkOrder> => {
    const { data } = await apiClient.post<WorkOrder>(`/work-orders/${id}/complete`, {})
    return data
  },

  /**
   * Add operation to work order
   */
  addOperation: async (id: number, operation: AddOperationRequest): Promise<any> => {
    const { data } = await apiClient.post(`/work-orders/${id}/operations`, operation)
    return data
  },

  /**
   * Add material to work order
   */
  addMaterial: async (id: number, material: AddMaterialRequest): Promise<any> => {
    const { data } = await apiClient.post(`/work-orders/${id}/materials`, material)
    return data
  },
}
