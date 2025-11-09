/**
 * NCR Types
 *
 * TypeScript types matching backend NCR entity and DTOs
 */

export type NCRStatus = 'OPEN' | 'INVESTIGATING' | 'CORRECTIVE_ACTION' | 'CLOSED' | 'REJECTED'
export type DefectType = 'MATERIAL' | 'PROCESS' | 'EQUIPMENT' | 'WORKMANSHIP' | 'DESIGN' | 'OTHER'

export interface NCR {
  id: number
  organization_id: number
  plant_id: number
  ncr_number: string
  status: NCRStatus
  defect_type: DefectType
  work_order_id: number | null
  material_id: number | null
  quantity_affected: number
  description: string
  root_cause: string | null
  corrective_action: string | null
  preventive_action: string | null
  reported_by: number
  assigned_to: number | null
  reported_at: string
  closed_at: string | null
  created_at: string
  updated_at: string | null
}

export interface CreateNCRDTO {
  organization_id: number
  plant_id: number
  ncr_number: string
  defect_type: DefectType
  work_order_id?: number
  material_id?: number
  quantity_affected: number
  description: string
  reported_by: number
}

export interface UpdateNCRDTO {
  status?: NCRStatus
  root_cause?: string
  corrective_action?: string
  preventive_action?: string
  assigned_to?: number
}

export interface NCRListResponse {
  items: NCR[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface NCRFilters {
  plant_id?: number
  status?: NCRStatus
  defect_type?: DefectType
  page?: number
  page_size?: number
}
