/**
 * Shift Service
 *
 * API client for Shift CRUD operations and handover management
 */
import axios from 'axios'
import type {
  Shift,
  CreateShiftDTO,
  UpdateShiftDTO,
  ShiftListResponse,
  ShiftFilters,
  ShiftHandover,
  CreateShiftHandoverDTO,
  ShiftHandoverListResponse,
  ShiftHandoverFilters,
} from '../types/shift.types'

const API_URL = '/api/v1/shifts'

export const shiftService = {
  /**
   * Get all shifts with optional filters
   */
  getAll: async (filters?: ShiftFilters): Promise<ShiftListResponse> => {
    const { data } = await axios.get(API_URL, { params: filters })
    return data
  },

  /**
   * Get shift by ID
   */
  getById: async (id: number): Promise<Shift> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  /**
   * Create new shift
   */
  create: async (shift: CreateShiftDTO): Promise<Shift> => {
    const { data } = await axios.post(API_URL, shift)
    return data
  },

  /**
   * Update existing shift
   */
  update: async (id: number, shift: UpdateShiftDTO): Promise<Shift> => {
    const { data } = await axios.put(`${API_URL}/${id}`, shift)
    return data
  },

  /**
   * Create shift handover
   */
  createHandover: async (handover: CreateShiftHandoverDTO): Promise<ShiftHandover> => {
    const { data } = await axios.post(`${API_URL}/handovers`, handover)
    return data
  },

  /**
   * Get all handovers with optional filters
   */
  getHandovers: async (filters?: ShiftHandoverFilters): Promise<ShiftHandoverListResponse> => {
    const { data } = await axios.get(`${API_URL}/handovers`, { params: filters })
    return data
  },

  /**
   * Acknowledge shift handover
   */
  acknowledgeHandover: async (handoverId: number): Promise<ShiftHandover> => {
    const { data } = await axios.post(`${API_URL}/handovers/${handoverId}/acknowledge`, {})
    return data
  },
}
