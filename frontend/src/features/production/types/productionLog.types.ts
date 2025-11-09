/**
 * Production Log Types
 *
 * TypeScript types matching backend ProductionLog entity and DTOs
 */

export interface ProductionLog {
  id: number
  organization_id: number
  plant_id: number
  work_order_id: number
  operation_id?: number
  machine_id?: number
  timestamp: string  // ISO datetime
  quantity_produced: number
  quantity_scrapped: number
  quantity_reworked: number
  operator_id?: number
  shift_id?: number
  notes?: string
  custom_metadata?: Record<string, any>
}

export interface ProductionLogCreateRequest {
  organization_id: number
  plant_id: number
  work_order_id: number
  operation_id?: number
  machine_id?: number
  quantity_produced: number
  quantity_scrapped?: number
  quantity_reworked?: number
  operator_id?: number
  shift_id?: number
  notes?: string
  custom_metadata?: Record<string, any>
}

export interface ProductionLogListResponse {
  items: ProductionLog[]
  total: number
  page: number
  page_size: number
}

export interface ProductionSummary {
  work_order_id: number
  total_produced: number
  total_scrapped: number
  total_reworked: number
  yield_rate: number  // Percentage 0-100
  log_count: number
  first_log: string  // ISO datetime
  last_log: string   // ISO datetime
}

export interface ProductionLogFilters {
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}
