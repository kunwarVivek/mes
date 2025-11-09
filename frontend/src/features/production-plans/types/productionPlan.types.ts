/**
 * Production Plan Types
 *
 * TypeScript types matching backend ProductionPlan entity and DTOs
 */

export type PlanStatus = 'DRAFT' | 'APPROVED' | 'IN_PROGRESS' | 'COMPLETED'

export interface ProductionPlanItem {
  id: number
  production_plan_id: number
  material_id: number
  planned_quantity: number
  unit_of_measure_id: number
  target_completion_date: string
  created_at: string
  updated_at?: string
}

export interface ProductionPlan {
  id: number
  organization_id: number
  plant_id: number
  plan_code: string
  plan_name: string
  start_date: string
  end_date: string
  status: PlanStatus
  created_by_user_id: number
  approved_by_user_id?: number
  approval_date?: string
  created_at: string
  updated_at?: string
  items?: ProductionPlanItem[]
}

export interface CreateProductionPlanDTO {
  plan_code: string
  plan_name: string
  start_date: string
  end_date: string
  status?: PlanStatus
}

export interface UpdateProductionPlanDTO {
  plan_name?: string
  start_date?: string
  end_date?: string
  status?: PlanStatus
}

export interface ProductionPlanListResponse {
  items: ProductionPlan[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ProductionPlanFilters {
  status?: PlanStatus
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}
