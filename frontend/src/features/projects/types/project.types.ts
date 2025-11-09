/**
 * Project Types
 *
 * TypeScript interfaces for Project domain entities and DTOs
 * Aligned with backend DTOs in app/application/dtos/project_dto.py
 */

export enum ProjectStatus {
  PLANNING = 'PLANNING',
  ACTIVE = 'ACTIVE',
  ON_HOLD = 'ON_HOLD',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
}

export interface Project {
  id: number
  organization_id: number
  plant_id: number
  project_code: string
  project_name: string
  description?: string
  status: ProjectStatus
  bom_id?: number
  planned_start_date?: string
  planned_end_date?: string
  actual_start_date?: string
  actual_end_date?: string
  priority: number
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface ProjectCreateRequest {
  organization_id: number
  plant_id: number
  project_code: string
  project_name: string
  description?: string
  bom_id?: number
  planned_start_date?: string
  planned_end_date?: string
  status?: ProjectStatus
  priority?: number
}

export interface ProjectUpdateRequest {
  project_name?: string
  description?: string
  bom_id?: number
  planned_start_date?: string
  planned_end_date?: string
  actual_start_date?: string
  actual_end_date?: string
  status?: ProjectStatus
  priority?: number
  is_active?: boolean
}

export interface ProjectListResponse {
  items: Project[]
  total: number
  page: number
  page_size: number
}

export interface ProjectFilters {
  plant_id?: number
  status?: ProjectStatus
  page?: number
  page_size?: number
}
