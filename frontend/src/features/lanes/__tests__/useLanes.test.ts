/**
 * useLanes Hooks Tests
 *
 * TDD RED Phase: Test TanStack Query hooks integration
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { lanesService } from '../services/lanes.service'
import {
  useLanes,
  useLane,
  useLaneCapacity,
  useLaneAssignments,
  useCreateAssignment,
  useUpdateAssignment,
  useDeleteAssignment,
} from '../hooks/useLanes'
import React from 'react'

// Mock the service
vi.mock('../services/lanes.service')
const mockedService = vi.mocked(lanesService)

// Mock auth store
vi.mock('@/stores/auth.store', () => ({
  useAuthStore: vi.fn(() => ({
    currentPlant: { id: 100, plant_code: 'P1', plant_name: 'Plant 1' },
    currentOrg: { id: 1, org_code: 'ORG1', org_name: 'Organization 1' },
  })),
}))

describe('Lane Hooks', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)

  describe('useLanes', () => {
    it('should fetch lanes for plant', async () => {
      const mockResponse = {
        items: [
          {
            id: 1,
            plant_id: 100,
            lane_code: 'L001',
            lane_name: 'Assembly Line 1',
            capacity_per_day: 1000,
            is_active: true,
            created_at: '2025-01-01T00:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        page_size: 10,
      }

      mockedService.listLanes.mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useLanes(100), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(mockedService.listLanes).toHaveBeenCalledWith({ plant_id: 100 })
      expect(result.current.data?.items).toHaveLength(1)
      expect(result.current.data?.items[0].lane_code).toBe('L001')
    })

    it('should handle loading state', () => {
      mockedService.listLanes.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      const { result } = renderHook(() => useLanes(100), { wrapper })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeUndefined()
    })
  })

  describe('useLane', () => {
    it('should fetch single lane', async () => {
      const mockLane = {
        id: 1,
        plant_id: 100,
        lane_code: 'L001',
        lane_name: 'Assembly Line 1',
        capacity_per_day: 1000,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      }

      mockedService.getLane.mockResolvedValueOnce(mockLane)

      const { result } = renderHook(() => useLane(1), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(mockedService.getLane).toHaveBeenCalledWith(1)
      expect(result.current.data?.lane_code).toBe('L001')
    })
  })

  describe('useLaneCapacity', () => {
    it('should fetch capacity for lane and date', async () => {
      const mockCapacity = {
        lane_id: 1,
        date: '2025-01-15',
        total_capacity: 1000,
        allocated_capacity: 800,
        available_capacity: 200,
        utilization_rate: 80,
        assignment_count: 3,
      }

      mockedService.getLaneCapacity.mockResolvedValueOnce(mockCapacity)

      const { result } = renderHook(() => useLaneCapacity(1, '2025-01-15'), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(mockedService.getLaneCapacity).toHaveBeenCalledWith(1, '2025-01-15')
      expect(result.current.data?.utilization_rate).toBe(80)
    })
  })

  describe('useLaneAssignments', () => {
    it('should fetch assignments with date range', async () => {
      const mockResponse = {
        items: [
          {
            id: 1,
            organization_id: 1,
            plant_id: 100,
            lane_id: 1,
            work_order_id: 500,
            scheduled_start: '2025-01-15',
            scheduled_end: '2025-01-20',
            allocated_capacity: 500,
            priority: 1,
            status: 'PLANNED' as const,
            created_at: '2025-01-01T00:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        page_size: 10,
      }

      mockedService.listAssignments.mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(
        () =>
          useLaneAssignments({
            lane_id: 1,
            start_date: '2025-01-15',
            end_date: '2025-01-20',
          }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(mockedService.listAssignments).toHaveBeenCalledWith({
        lane_id: 1,
        start_date: '2025-01-15',
        end_date: '2025-01-20',
      })
      expect(result.current.data?.items).toHaveLength(1)
    })
  })

  describe('useCreateAssignment', () => {
    it('should create assignment and invalidate queries', async () => {
      const createRequest = {
        organization_id: 1,
        plant_id: 100,
        lane_id: 1,
        work_order_id: 500,
        scheduled_start: '2025-01-15',
        scheduled_end: '2025-01-20',
        allocated_capacity: 500,
        priority: 1,
      }

      const mockResponse = {
        id: 1,
        ...createRequest,
        status: 'PLANNED' as const,
        created_at: '2025-01-01T00:00:00Z',
      }

      mockedService.createAssignment.mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useCreateAssignment(), { wrapper })

      await result.current.mutateAsync(createRequest)

      expect(mockedService.createAssignment).toHaveBeenCalledWith(createRequest)
    })
  })

  describe('useUpdateAssignment', () => {
    it('should update assignment and invalidate queries', async () => {
      const updateRequest = {
        allocated_capacity: 600,
        status: 'ACTIVE' as const,
      }

      const mockResponse = {
        id: 1,
        organization_id: 1,
        plant_id: 100,
        lane_id: 1,
        work_order_id: 500,
        scheduled_start: '2025-01-15',
        scheduled_end: '2025-01-20',
        allocated_capacity: 600,
        priority: 1,
        status: 'ACTIVE' as const,
        created_at: '2025-01-01T00:00:00Z',
      }

      mockedService.updateAssignment.mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useUpdateAssignment(), { wrapper })

      await result.current.mutateAsync({ id: 1, data: updateRequest })

      expect(mockedService.updateAssignment).toHaveBeenCalledWith(1, updateRequest)
    })
  })

  describe('useDeleteAssignment', () => {
    it('should delete assignment and invalidate queries', async () => {
      mockedService.deleteAssignment.mockResolvedValueOnce()

      const { result } = renderHook(() => useDeleteAssignment(), { wrapper })

      await result.current.mutateAsync(1)

      expect(mockedService.deleteAssignment).toHaveBeenCalledWith(1)
    })
  })
})
