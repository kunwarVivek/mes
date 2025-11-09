/**
 * MRP Types
 *
 * TypeScript types matching backend MRPRun and PlannedOrder entities
 */

export type MRPStatus = 'DRAFT' | 'RUNNING' | 'COMPLETED' | 'FAILED'
export type PlannedOrderType = 'PRODUCTION' | 'PURCHASE'
export type PlannedOrderStatus = 'PROPOSED' | 'APPROVED' | 'RELEASED'

export interface MRPRun {
  id: number
  organization_id: number
  run_code: string
  run_name: string
  run_date: string
  planning_horizon_days: number
  status: MRPStatus
  created_by_user_id: number
  created_at: string
  updated_at?: string
}

export interface PlannedOrder {
  id: number
  mrp_run_id: number
  material_id: number
  quantity: number
  due_date: string
  order_type: PlannedOrderType
  status: PlannedOrderStatus
  created_at: string
  updated_at?: string
}

export interface CreateMRPRunDTO {
  organization_id: number
  run_code: string
  run_name: string
  run_date: string
  planning_horizon_days: number
  status?: MRPStatus
  created_by_user_id: number
}

export interface UpdateMRPRunDTO {
  run_name?: string
  run_date?: string
  planning_horizon_days?: number
  status?: MRPStatus
}

export interface MRPRunListResponse {
  items: MRPRun[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MRPRunFilters {
  search?: string
  status?: MRPStatus
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}
