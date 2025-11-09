/**
 * Shift Types
 *
 * TypeScript types matching backend Shift entity and DTOs
 */

export interface Shift {
  id: number
  organization_id: number
  plant_id: number
  shift_code: string
  shift_name: string
  start_time: string // HH:MM:SS format from backend
  end_time: string // HH:MM:SS format from backend
  production_target: number
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface CreateShiftDTO {
  shift_name: string
  shift_code: string
  start_time: string // HH:MM:SS format
  end_time: string // HH:MM:SS format
  production_target: number
  is_active?: boolean
}

export interface UpdateShiftDTO {
  shift_name?: string
  start_time?: string
  end_time?: string
  production_target?: number
  is_active?: boolean
}

export interface ShiftListResponse {
  items: Shift[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ShiftFilters {
  is_active?: boolean
  shift_code?: string
  page?: number
  page_size?: number
}

// Shift Handover Types
export interface ShiftHandover {
  id: number
  organization_id: number
  plant_id: number
  from_shift_id: number
  to_shift_id: number
  handover_date: string
  wip_quantity: number
  production_summary: string
  quality_issues?: string
  machine_status?: string
  material_status?: string
  safety_incidents?: string
  handover_by_user_id: number
  acknowledged_by_user_id?: number
  acknowledged_at?: string
  created_at: string
}

export interface CreateShiftHandoverDTO {
  from_shift_id: number
  to_shift_id: number
  handover_date: string
  wip_quantity: number
  production_summary: string
  quality_issues?: string
  machine_status?: string
  material_status?: string
  safety_incidents?: string
}

export interface ShiftHandoverListResponse {
  items: ShiftHandover[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ShiftHandoverFilters {
  from_shift_id?: number
  to_shift_id?: number
  acknowledged?: boolean
  page?: number
  page_size?: number
}
