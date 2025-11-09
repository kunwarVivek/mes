/**
 * Work Order Types
 *
 * TypeScript types matching backend WorkOrder entity and DTOs
 */

export type OrderType = 'PRODUCTION' | 'REWORK' | 'ASSEMBLY'
export type OrderStatus = 'PLANNED' | 'RELEASED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'

export interface WorkOrderOperation {
  id: number
  work_order_id: number
  operation_number: number
  operation_name: string
  work_center_id: number
  setup_time_minutes: number
  run_time_per_unit_minutes: number
  status: string
  created_at: string
  updated_at?: string
}

export interface WorkOrderMaterial {
  id: number
  work_order_id: number
  material_id: number
  planned_quantity: number
  actual_quantity: number
  unit_of_measure_id: number
  backflush: boolean
  created_at: string
  updated_at?: string
}

export interface WorkOrder {
  id: number
  organization_id: number
  plant_id: number
  work_order_number: string
  material_id: number
  order_type: OrderType
  order_status: OrderStatus
  planned_quantity: number
  actual_quantity: number
  start_date_planned?: string
  start_date_actual?: string
  end_date_planned?: string
  end_date_actual?: string
  priority: number
  created_by_user_id: number
  created_at: string
  updated_at?: string
  operations?: WorkOrderOperation[]
  materials?: WorkOrderMaterial[]
}

export interface CreateWorkOrderDTO {
  material_id: number
  order_type?: OrderType
  planned_quantity: number
  start_date_planned?: string
  end_date_planned?: string
  priority?: number
}

export interface UpdateWorkOrderDTO {
  planned_quantity?: number
  actual_quantity?: number
  start_date_planned?: string
  end_date_planned?: string
  priority?: number
  order_status?: OrderStatus
}

export interface WorkOrderListResponse {
  items: WorkOrder[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface WorkOrderFilters {
  status?: OrderStatus
  material_id?: number
  priority?: number
  page?: number
  page_size?: number
}
