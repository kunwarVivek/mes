/**
 * Projects Service
 *
 * API client for Projects CRUD operations
 */
import apiClient from '../../../lib/api-client'
import type {
  Project,
  ProjectCreateRequest,
  ProjectUpdateRequest,
  ProjectListResponse,
  ProjectFilters,
} from '../types/project.types'

const API_URL = '/projects'

export const projectsService = {
  /**
   * Get all projects with optional filters
   */
  list: async (filters?: ProjectFilters): Promise<ProjectListResponse> => {
    const { data } = await apiClient.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get project by ID
   */
  getById: async (id: number): Promise<Project> => {
    const { data } = await apiClient.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Create new project
   */
  create: async (project: ProjectCreateRequest): Promise<Project> => {
    const { data } = await apiClient.post(API_URL, project)
    return data
  },

  /**
   * Update existing project
   */
  update: async (id: number, project: ProjectUpdateRequest): Promise<Project> => {
    const { data } = await apiClient.put(`${API_URL}/${id}`, project)
    return data
  },

  /**
   * Delete project
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${API_URL}/${id}`)
  },
}
