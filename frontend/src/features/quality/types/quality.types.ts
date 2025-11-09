/**
 * Quality Types
 *
 * TypeScript types matching backend NCR entity and DTOs
 */

export type NCRStatus = 'OPEN' | 'IN_REVIEW' | 'RESOLVED' | 'CLOSED'
export type DefectType = 'DIMENSIONAL' | 'VISUAL' | 'FUNCTIONAL' | 'MATERIAL' | 'OTHER'

export interface NCR {
  id: number
  organization_id: number
  plant_id: number
  ncr_number: string
  work_order_id: number
  material_id: number
  defect_type: DefectType
  defect_description: string
  quantity_defective: number
  status: NCRStatus
  reported_by_user_id: number
  attachment_urls?: string[]
  resolution_notes?: string
  resolved_by_user_id?: number
  resolved_at?: string
  created_at: string
  updated_at?: string
}

export interface CreateNCRDTO {
  ncr_number: string
  work_order_id: number
  material_id: number
  defect_type: DefectType
  defect_description: string
  quantity_defective: number
  reported_by_user_id: number
  attachment_urls?: string[]
}

export interface UpdateNCRStatusDTO {
  status: NCRStatus
  resolution_notes?: string
  resolved_by_user_id?: number
}

export interface NCRListResponse {
  items: NCR[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface NCRFilters {
  search?: string
  status?: NCRStatus
  defect_type?: DefectType
  work_order_id?: number
  page?: number
  page_size?: number
}
