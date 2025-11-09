/**
 * Production Plan Service
 *
 * API client for Production Plan CRUD operations
 */
import axios from 'axios'
import type {
  ProductionPlan,
  CreateProductionPlanDTO,
  UpdateProductionPlanDTO,
  ProductionPlanListResponse,
  ProductionPlanFilters,
} from '../types/production.types'

const API_URL = '/api/v1/production-plans'

export const productionService = {
  /**
   * Get all production plans with optional filters
   */
  getAll: async (filters?: ProductionPlanFilters): Promise<ProductionPlanListResponse> => {
    const { data } = await axios.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get production plan by ID
   */
  getById: async (id: number): Promise<ProductionPlan> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Create new production plan
   */
  create: async (plan: CreateProductionPlanDTO): Promise<ProductionPlan> => {
    const { data } = await axios.post(API_URL, plan)
    return data
  },

  /**
   * Update existing production plan
   */
  update: async (id: number, plan: UpdateProductionPlanDTO): Promise<ProductionPlan> => {
    const { data } = await axios.put(`${API_URL}/${id}`, plan)
    return data
  },

  /**
   * Delete production plan
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },
}
