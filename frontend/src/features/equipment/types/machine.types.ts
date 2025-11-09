/**
 * Machine Types
 *
 * TypeScript types matching backend Machine entity and DTOs
 */

export type MachineStatus =
  | 'AVAILABLE'
  | 'RUNNING'
  | 'IDLE'
  | 'DOWN'
  | 'SETUP'
  | 'MAINTENANCE'

export interface Machine {
  id: number
  organization_id: number
  plant_id: number
  machine_code: string
  machine_name: string
  description: string
  work_center_id: number
  status: MachineStatus
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface CreateMachineDTO {
  organization_id: number
  plant_id: number
  machine_code: string
  machine_name: string
  description: string
  work_center_id: number
  status: MachineStatus
}

export interface UpdateMachineDTO {
  machine_name?: string
  description?: string
  work_center_id?: number
  status?: MachineStatus
  is_active?: boolean
}

export interface MachineStatusUpdateDTO {
  status: MachineStatus
  notes?: string
}

export interface MachineStatusHistory {
  id: number
  machine_id: number
  status: MachineStatus
  started_at: string
  ended_at?: string
  notes?: string
  duration_minutes?: number
}

export interface MachineStatusUpdateResponse {
  machine: Machine
  status_history: MachineStatusHistory
}

export interface OEEMetrics {
  availability: number // 0-1
  performance: number // 0-1
  quality: number // 0-1
  oee_score: number // 0-1
}

export interface MachineListResponse {
  items: Machine[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MachineFilters {
  search?: string
  status?: MachineStatus
  work_center_id?: number
  plant_id?: number
  is_active?: boolean
  page?: number
  page_size?: number
}
