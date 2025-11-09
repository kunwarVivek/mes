/**
 * BOM Service
 *
 * API client for BOM CRUD operations including hierarchical tree structure
 * Note: Backend API not yet implemented - will be connected later
 */
import apiClient from '../../../lib/api-client'
import type {
  BOM,
  CreateBOMDTO,
  UpdateBOMDTO,
  BOMListResponse,
  BOMFilters,
  BOMLineWithChildren,
  CreateBOMLineDTO,
  UpdateBOMLineDTO,
} from '../types/bom.types'

const API_URL = '/boms'

/**
 * BOM with tree structure including nested children
 */
export interface BOMTree extends BOM {
  lines: BOMLineWithChildren[]
}

export const bomService = {
  /**
   * Get all BOMs with optional filters
   */
  getAll: async (filters?: BOMFilters): Promise<BOMListResponse> => {
    const { data } = await apiClient.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get BOM by ID
   */
  getById: async (id: number): Promise<BOM> => {
    const { data } = await apiClient.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Get BOM tree structure with nested children
   */
  getTree: async (id: number): Promise<BOMTree> => {
    const { data } = await apiClient.get(`${API_URL}/${id}/tree`)
    return data
  },

  /**
   * Create new BOM
   */
  create: async (bom: CreateBOMDTO): Promise<BOM> => {
    const { data } = await apiClient.post(API_URL, bom)
    return data
  },

  /**
   * Update existing BOM
   */
  update: async (id: number, bom: UpdateBOMDTO): Promise<BOM> => {
    const { data } = await apiClient.put(`${API_URL}/${id}`, bom)
    return data
  },

  /**
   * Delete BOM
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${API_URL}/${id}`)
  },

  /**
   * Search BOMs by query
   */
  search: async (query: string, limit: number = 20): Promise<BOM[]> => {
    const { data } = await apiClient.get(`${API_URL}/search`, {
      params: { q: query, limit },
    })
    return data
  },

  // ============================================
  // BOM Line Operations
  // ============================================

  /**
   * Create BOM line
   */
  createLine: async (line: CreateBOMLineDTO): Promise<BOMLineWithChildren> => {
    const { data } = await apiClient.post(`${API_URL}/lines`, line)
    return data
  },

  /**
   * Update BOM line
   */
  updateLine: async (id: number, line: UpdateBOMLineDTO): Promise<BOMLineWithChildren> => {
    const { data } = await apiClient.put(`${API_URL}/lines/${id}`, line)
    return data
  },

  /**
   * Delete BOM line
   */
  deleteLine: async (id: number): Promise<void> => {
    await apiClient.delete(`${API_URL}/lines/${id}`)
  },
}
