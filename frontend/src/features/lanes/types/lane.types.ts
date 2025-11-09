/**
 * Lane Types
 *
 * TypeScript interfaces for Lane Scheduling domain
 */

export enum LaneAssignmentStatus {
  PLANNED = 'PLANNED',
  ACTIVE = 'ACTIVE',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
}

export interface Lane {
  id: number
  plant_id: number
  lane_code: string
  lane_name: string
  capacity_per_day: string  // Backend uses Decimal, transmitted as string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface LaneAssignment {
  id: number
  organization_id: number
  plant_id: number
  lane_id: number
  work_order_id: number
  project_id?: number
  scheduled_start: string  // Date string YYYY-MM-DD
  scheduled_end: string    // Date string YYYY-MM-DD
  allocated_capacity: string  // Backend uses Decimal, transmitted as string
  priority: number
  status: LaneAssignmentStatus
  notes?: string
  created_at: string
  updated_at?: string
}

export interface LaneCapacity {
  lane_id: number
  date: string  // Date string YYYY-MM-DD
  total_capacity: string  // Backend uses Decimal, transmitted as string
  allocated_capacity: string  // Backend uses Decimal, transmitted as string
  available_capacity: string  // Backend uses Decimal, transmitted as string
  utilization_rate: number  // Percentage 0-100+
  assignment_count: number
}

export interface LaneListResponse {
  items: Lane[]
  total: number
  page: number
  page_size: number
}

export interface LaneAssignmentListResponse {
  items: LaneAssignment[]
  total: number
  page: number
  page_size: number
}

export interface LaneAssignmentCreateRequest {
  organization_id: number
  plant_id: number
  lane_id: number
  work_order_id: number
  project_id?: number
  scheduled_start: string
  scheduled_end: string
  allocated_capacity: string  // Backend uses Decimal, transmitted as string
  priority?: number
  notes?: string
}

export interface LaneAssignmentUpdateRequest {
  scheduled_start?: string
  scheduled_end?: string
  allocated_capacity?: string  // Backend uses Decimal, transmitted as string
  priority?: number
  status?: LaneAssignmentStatus
  notes?: string
}
