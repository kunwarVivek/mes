/**
 * Material Service
 *
 * API client for Material CRUD operations
 */
import apiClient from '@/lib/api-client'
import type { CreateMaterialFormData, UpdateMaterialFormData } from '../schemas/material.schema'

export interface Material {
  id: number
  organization_id: number
  plant_id: number
  material_number: string
  material_name: string
  description?: string
  material_category_id: number
  base_uom_id: number
  procurement_type: string
  mrp_type: string
  safety_stock: number
  reorder_point: number
  lot_size: number
  lead_time_days: number
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface MaterialListResponse {
  items: Material[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MaterialListParams {
  page?: number
  page_size?: number
  search?: string
  procurement_type?: string
  mrp_type?: string
  is_active?: boolean
}

export const materialService = {
  /**
   * List materials with optional filters and pagination
   */
  list: async (params?: MaterialListParams): Promise<MaterialListResponse> => {
    const { data } = await apiClient.get<MaterialListResponse>('/materials', { params })
    return data
  },

  /**
   * Get material by ID
   */
  get: async (id: number): Promise<Material> => {
    const { data } = await apiClient.get<Material>(`/materials/${id}`)
    return data
  },

  /**
   * Create new material
   */
  create: async (material: CreateMaterialFormData): Promise<Material> => {
    const { data } = await apiClient.post<Material>('/materials', material)
    return data
  },

  /**
   * Update existing material
   */
  update: async (id: number, material: UpdateMaterialFormData): Promise<Material> => {
    const { data } = await apiClient.put<Material>(`/materials/${id}`, material)
    return data
  },

  /**
   * Delete material
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/materials/${id}`)
  },
}
