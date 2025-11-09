/**
 * BOM (Bill of Materials) Types
 *
 * TypeScript types matching backend BOM entity and DTOs
 */

export type BOMType = 'PRODUCTION' | 'ENGINEERING' | 'PLANNING'

export interface BOMLine {
  id: number
  bom_header_id: number
  line_number: number
  component_material_id: number
  quantity: number
  unit_of_measure_id: number
  scrap_factor: number
  operation_number?: number
  is_phantom: boolean
  backflush: boolean
  created_at: string
  updated_at?: string
}

/**
 * BOM Line with optional children for tree view
 */
export interface BOMLineWithChildren extends BOMLine {
  component_material_name?: string
  unit_of_measure?: string
  children?: BOMLineWithChildren[]
}

export interface BOM {
  id: number
  organization_id: number
  plant_id: number
  bom_number: string
  material_id: number
  bom_version: number
  bom_name: string
  bom_type: BOMType
  base_quantity: number
  unit_of_measure_id: number
  effective_start_date?: string
  effective_end_date?: string
  is_active: boolean
  created_by_user_id: number
  created_at: string
  updated_at?: string
  bom_lines?: BOMLine[]
}

export interface CreateBOMDTO {
  bom_number: string
  material_id: number
  bom_name: string
  bom_type: BOMType
  base_quantity: number
  unit_of_measure_id: number
  effective_start_date?: string
  effective_end_date?: string
  bom_version?: number
}

export interface UpdateBOMDTO {
  bom_name?: string
  bom_type?: BOMType
  base_quantity?: number
  effective_start_date?: string
  effective_end_date?: string
  is_active?: boolean
}

export interface BOMListResponse {
  items: BOM[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface BOMFilters {
  material_id?: number
  bom_type?: BOMType
  is_active?: boolean
  page?: number
  page_size?: number
}

/**
 * DTO for creating BOM lines
 */
export interface CreateBOMLineDTO {
  bom_header_id: number
  component_material_id: number
  quantity: number
  unit_of_measure_id: number
  line_number: number
  scrap_factor?: number
  is_phantom?: boolean
  backflush?: boolean
  operation_number?: number
}

/**
 * DTO for updating BOM lines
 */
export interface UpdateBOMLineDTO {
  component_material_id?: number
  quantity?: number
  unit_of_measure_id?: number
  line_number?: number
  scrap_factor?: number
  is_phantom?: boolean
  backflush?: boolean
  operation_number?: number
}
