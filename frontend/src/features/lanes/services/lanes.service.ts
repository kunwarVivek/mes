/**
 * Lanes Service
 *
 * API client for Lane Scheduling operations
 */
import axios from 'axios'
import type {
  Lane,
  LaneListResponse,
  LaneAssignment,
  LaneAssignmentListResponse,
  LaneCapacity,
  LaneAssignmentCreateRequest,
  LaneAssignmentUpdateRequest,
} from '../types/lane.types'

const API_BASE_URL = '/api/v1/lanes'

export const lanesService = {
  /**
   * List all lanes with optional filters
   */
  listLanes: async (params?: {
    plant_id?: number
    is_active?: boolean
    page?: number
    page_size?: number
  }): Promise<LaneListResponse> => {
    const { data } = await axios.get(API_BASE_URL, { params })
    return data
  },

  /**
   * Get single lane by ID
   */
  getLane: async (laneId: number): Promise<Lane> => {
    const { data } = await axios.get(`${API_BASE_URL}/${laneId}`)
    return data
  },

  /**
   * Get lane capacity for specific date
   */
  getLaneCapacity: async (laneId: number, date: string): Promise<LaneCapacity> => {
    const { data } = await axios.get(`${API_BASE_URL}/${laneId}/capacity`, {
      params: { date },
    })
    return data
  },

  /**
   * List assignments with filters
   */
  listAssignments: async (params?: {
    lane_id?: number
    plant_id?: number
    start_date?: string
    end_date?: string
    status?: string
    page?: number
    page_size?: number
  }): Promise<LaneAssignmentListResponse> => {
    const { data } = await axios.get(`${API_BASE_URL}/assignments`, { params })
    return data
  },

  /**
   * Get single assignment by ID
   */
  getAssignment: async (assignmentId: number): Promise<LaneAssignment> => {
    const { data } = await axios.get(`${API_BASE_URL}/assignments/${assignmentId}`)
    return data
  },

  /**
   * Create new lane assignment
   */
  createAssignment: async (
    request: LaneAssignmentCreateRequest
  ): Promise<LaneAssignment> => {
    const { data } = await axios.post(`${API_BASE_URL}/assignments`, request)
    return data
  },

  /**
   * Update existing lane assignment
   */
  updateAssignment: async (
    assignmentId: number,
    request: LaneAssignmentUpdateRequest
  ): Promise<LaneAssignment> => {
    const { data } = await axios.put(`${API_BASE_URL}/assignments/${assignmentId}`, request)
    return data
  },

  /**
   * Delete lane assignment
   */
  deleteAssignment: async (assignmentId: number): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/assignments/${assignmentId}`)
  },
}
