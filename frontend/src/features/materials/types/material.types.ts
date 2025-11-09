/**
 * Material Types
 *
 * TypeScript types matching backend Material entity and DTOs
 */

export type ProcurementType = 'PURCHASE' | 'MANUFACTURE' | 'BOTH'
export type MRPType = 'MRP' | 'REORDER'

export interface Material {
  id: number
  organization_id: number
  plant_id: number
  material_number: string
  material_name: string
  description?: string
  material_category_id: number
  base_uom_id: number
  procurement_type: ProcurementType
  mrp_type: MRPType
  safety_stock: number
  reorder_point: number
  lot_size: number
  lead_time_days: number
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface CreateMaterialDTO {
  organization_id: number
  plant_id: number
  material_number: string
  material_name: string
  description?: string
  material_category_id: number
  base_uom_id: number
  procurement_type: ProcurementType
  mrp_type: MRPType
  safety_stock?: number
  reorder_point?: number
  lot_size?: number
  lead_time_days?: number
}

export interface UpdateMaterialDTO {
  material_name?: string
  description?: string
  material_category_id?: number
  procurement_type?: ProcurementType
  mrp_type?: MRPType
  safety_stock?: number
  reorder_point?: number
  lot_size?: number
  lead_time_days?: number
  is_active?: boolean
}

export interface MaterialListResponse {
  items: Material[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MaterialFilters {
  search?: string
  category_id?: number
  procurement_type?: ProcurementType
  mrp_type?: MRPType
  is_active?: boolean
  page?: number
  page_size?: number
}
