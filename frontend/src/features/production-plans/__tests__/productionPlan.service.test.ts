/**
 * Production Plan Service Tests
 *
 * TDD: Testing API service layer with mocked axios
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { productionPlanService } from '../services/productionPlan.service'
import type { CreateProductionPlanDTO, UpdateProductionPlanDTO } from '../types/productionPlan.types'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('productionPlanService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all production plans without filters', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              organization_id: 1,
              plant_id: 1,
              plan_code: 'PLAN001',
              plan_name: 'Q1 2024 Plan',
              start_date: '2024-01-01',
              end_date: '2024-03-31',
              status: 'DRAFT',
              created_by_user_id: 1,
              created_at: '2024-01-01T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 50,
          total_pages: 1,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await productionPlanService.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/production-plans', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should fetch production plans with filters', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0,
        },
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const filters = {
        status: 'APPROVED' as const,
        page: 1,
        page_size: 20,
      }

      const result = await productionPlanService.getAll(filters)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/production-plans', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getById', () => {
    it('should fetch production plan by ID', async () => {
      const mockPlan = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        plan_code: 'PLAN001',
        plan_name: 'Q1 2024 Plan',
        start_date: '2024-01-01',
        end_date: '2024-03-31',
        status: 'DRAFT',
        created_by_user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        items: [],
      }

      mockedAxios.get.mockResolvedValue({ data: mockPlan })

      const result = await productionPlanService.getById(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/production-plans/1')
      expect(result).toEqual(mockPlan)
    })
  })

  describe('create', () => {
    it('should create a new production plan', async () => {
      const newPlan: CreateProductionPlanDTO = {
        plan_code: 'PLAN002',
        plan_name: 'Q2 2024 Plan',
        start_date: '2024-04-01',
        end_date: '2024-06-30',
        status: 'DRAFT',
      }

      const mockResponse = {
        data: {
          id: 2,
          organization_id: 1,
          plant_id: 1,
          ...newPlan,
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await productionPlanService.create(newPlan)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/production-plans', newPlan)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('update', () => {
    it('should update an existing production plan', async () => {
      const updateData: UpdateProductionPlanDTO = {
        plan_name: 'Updated Q1 2024 Plan',
        status: 'APPROVED',
      }

      const mockResponse = {
        data: {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          plan_code: 'PLAN001',
          plan_name: 'Updated Q1 2024 Plan',
          start_date: '2024-01-01',
          end_date: '2024-03-31',
          status: 'APPROVED',
          created_by_user_id: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      }

      mockedAxios.put.mockResolvedValue(mockResponse)

      const result = await productionPlanService.update(1, updateData)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/v1/production-plans/1', updateData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('delete', () => {
    it('should delete a production plan', async () => {
      mockedAxios.delete.mockResolvedValue({ data: null })

      await productionPlanService.delete(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/production-plans/1')
    })
  })
})
