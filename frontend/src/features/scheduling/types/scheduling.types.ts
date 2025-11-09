/**
 * Scheduling Types
 *
 * TypeScript types matching backend ScheduledOperation entity
 */

export type ScheduledOperationStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'

export interface ScheduledOperation {
  id: number
  organization_id: number
  work_order_id: number
  operation_sequence: number
  operation_name: string
  machine_id?: number
  scheduled_start: string
  scheduled_end: string
  actual_start?: string
  actual_end?: string
  status: ScheduledOperationStatus
  priority: number
  created_at: string
  updated_at?: string
}

export interface CreateScheduledOperationDTO {
  organization_id: number
  work_order_id: number
  operation_sequence: number
  operation_name: string
  machine_id?: number
  scheduled_start: string
  scheduled_end: string
  status?: ScheduledOperationStatus
  priority: number
}

export interface UpdateScheduledOperationDTO {
  operation_name?: string
  machine_id?: number
  scheduled_start?: string
  scheduled_end?: string
  actual_start?: string
  actual_end?: string
  status?: ScheduledOperationStatus
  priority?: number
}

export interface ScheduledOperationListResponse {
  items: ScheduledOperation[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ScheduledOperationFilters {
  search?: string
  work_order_id?: number
  machine_id?: number
  status?: ScheduledOperationStatus
  start_date?: string
  end_date?: string
  priority_min?: number
  priority_max?: number
  page?: number
  page_size?: number
}
