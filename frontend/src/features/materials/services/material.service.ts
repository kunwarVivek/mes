/**
 * Material Service
 *
 * API client for Material CRUD operations
 */
import axios from 'axios'
import type {
  Material,
  CreateMaterialDTO,
  UpdateMaterialDTO,
  MaterialListResponse,
  MaterialFilters,
} from '../types/material.types'

const API_URL = '/api/v1/materials'

export const materialService = {
  /**
   * Get all materials with optional filters
   */
  getAll: async (filters?: MaterialFilters): Promise<MaterialListResponse> => {
    const { data } = await axios.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get material by ID
   */
  getById: async (id: number): Promise<Material> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Create new material
   */
  create: async (material: CreateMaterialDTO): Promise<Material> => {
    const { data } = await axios.post(API_URL, material)
    return data
  },

  /**
   * Update existing material
   */
  update: async (id: number, material: UpdateMaterialDTO): Promise<Material> => {
    const { data } = await axios.put(`${API_URL}/${id}`, material)
    return data
  },

  /**
   * Delete material (soft delete)
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },

  /**
   * Search materials by query
   */
  search: async (query: string, limit: number = 20): Promise<Material[]> => {
    const { data } = await axios.get(`${API_URL}/search`, {
      params: { q: query, limit },
    })
    return data
  },
}
