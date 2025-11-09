/**
 * Maintenance Types
 *
 * TypeScript types matching backend Maintenance entity and DTOs
 */

export type TriggerType = 'CALENDAR' | 'METER'
export type PMStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
export type DowntimeCategory =
  | 'BREAKDOWN'
  | 'PLANNED_MAINTENANCE'
  | 'CHANGEOVER'
  | 'NO_OPERATOR'
  | 'MATERIAL_SHORTAGE'

export interface PMSchedule {
  id: number
  organization_id: number
  plant_id: number
  schedule_code: string
  schedule_name: string
  machine_id: number
  trigger_type: TriggerType
  frequency_days: number | null
  meter_threshold: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreatePMScheduleDTO {
  schedule_code: string
  schedule_name: string
  machine_id: number
  trigger_type: TriggerType
  frequency_days?: number
  meter_threshold?: number
  is_active: boolean
}

export interface UpdatePMScheduleDTO {
  schedule_name?: string
  frequency_days?: number
  meter_threshold?: number
  is_active?: boolean
}

export interface PMScheduleFilters {
  machine_id?: number
  is_active?: boolean
}

export interface PMWorkOrder {
  id: number
  organization_id: number
  plant_id: number
  pm_schedule_id: number
  machine_id: number
  pm_number: string
  status: PMStatus
  scheduled_date: string
  due_date: string
  started_at: string | null
  completed_at: string | null
  notes: string | null
  created_at: string
}

export interface DowntimeEvent {
  id: number
  organization_id: number
  plant_id: number
  machine_id: number
  category: DowntimeCategory
  reason: string
  started_at: string
  ended_at: string | null
  duration_minutes: number | null
  notes: string | null
  created_at: string
}

export interface CreateDowntimeEventDTO {
  machine_id: number
  category: DowntimeCategory
  reason: string
  started_at: string
  ended_at?: string
  notes?: string
}

export interface UpdateDowntimeEventDTO {
  ended_at?: string
  notes?: string
}

export interface DowntimeEventFilters {
  machine_id?: number
  category?: DowntimeCategory
  start_date?: string
  end_date?: string
}

export interface MTBFMTTRMetrics {
  machine_id: number
  time_period_start: string
  time_period_end: string
  total_operating_time: number
  total_repair_time: number
  number_of_failures: number
  mtbf: number
  mttr: number
  availability: number
}
