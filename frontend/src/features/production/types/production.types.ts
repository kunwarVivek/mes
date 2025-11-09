/**
 * Production Plan Types
 *
 * TypeScript types matching backend ProductionPlan entity and DTOs
 */

export type ProductionPlanStatus = 'DRAFT' | 'APPROVED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'

export interface ProductionPlan {
  id: number
  organization_id: number
  plan_code: string
  plan_name: string
  start_date: string
  end_date: string
  status: ProductionPlanStatus
  created_by_user_id: number
  approved_by_user_id?: number
  approval_date?: string
  notes?: string
  created_at: string
  updated_at?: string
}

export interface CreateProductionPlanDTO {
  plan_code: string
  plan_name: string
  start_date: string
  end_date: string
  status: ProductionPlanStatus
  notes?: string
}

export interface UpdateProductionPlanDTO {
  plan_name?: string
  start_date?: string
  end_date?: string
  status?: ProductionPlanStatus
  notes?: string
}

export interface ProductionPlanListResponse {
  items: ProductionPlan[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ProductionPlanFilters {
  search?: string
  status?: ProductionPlanStatus
  start_date_from?: string
  start_date_to?: string
  page?: number
  page_size?: number
}
