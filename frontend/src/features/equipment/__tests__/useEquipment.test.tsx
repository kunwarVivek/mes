/**
 * Equipment Hooks Tests
 *
 * TDD: Testing React Query hooks with QueryClientProvider
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { equipmentService } from '../services/equipment.service'
import {
  useMachines,
  useMachine,
  useOEEMetrics,
  useDowntimeHistory,
  useUpdateMachineStatus,
} from '../hooks/useEquipment'
import { useAuthStore } from '@/stores/auth.store'
import React from 'react'

// Mock services
vi.mock('../services/equipment.service')
vi.mock('@/stores/auth.store')

const mockedEquipmentService = vi.mocked(equipmentService)
const mockedUseAuthStore = vi.mocked(useAuthStore)

// Create wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useEquipment hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Mock auth store
    mockedUseAuthStore.mockReturnValue({
      user: null,
      accessToken: 'test-token',
      refreshToken: null,
      isAuthenticated: true,
      currentOrg: { id: 1, org_code: 'ORG001', org_name: 'Test Org' },
      currentPlant: { id: 1, plant_code: 'PLT001', plant_name: 'Test Plant' },
      login: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
      setTokens: vi.fn(),
      setCurrentOrg: vi.fn(),
      setCurrentPlant: vi.fn(),
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('useMachines', () => {
    it('should fetch machines with current plant', async () => {
      const mockMachines = {
        items: [
          {
            id: 1,
            plant_id: 1,
            machine_code: 'MCH001',
            machine_name: 'CNC Machine 1',
            machine_type: 'CNC',
            status: 'RUNNING' as const,
            work_center_id: 1,
            capacity_per_hour: 100,
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: null,
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      }

      mockedEquipmentService.listMachines.mockResolvedValue(mockMachines)

      const { result } = renderHook(() => useMachines(), { wrapper: createWrapper() })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockMachines)
      expect(mockedEquipmentService.listMachines).toHaveBeenCalledWith({
        plant_id: 1,
        status: undefined,
      })
    })

    it('should fetch machines with status filter', async () => {
      const mockMachines = {
        items: [],
        total: 0,
        page: 1,
        page_size: 50,
      }

      mockedEquipmentService.listMachines.mockResolvedValue(mockMachines)

      const { result } = renderHook(() => useMachines('DOWN'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(mockedEquipmentService.listMachines).toHaveBeenCalledWith({
        plant_id: 1,
        status: 'DOWN',
      })
    })

    it('should not fetch when no plant is selected', async () => {
      mockedUseAuthStore.mockReturnValue({
        user: null,
        accessToken: 'test-token',
        refreshToken: null,
        isAuthenticated: true,
        currentOrg: { id: 1, org_code: 'ORG001', org_name: 'Test Org' },
        currentPlant: null,
        login: vi.fn(),
        logout: vi.fn(),
        updateUser: vi.fn(),
        setTokens: vi.fn(),
        setCurrentOrg: vi.fn(),
        setCurrentPlant: vi.fn(),
      })

      const { result } = renderHook(() => useMachines(), { wrapper: createWrapper() })

      expect(result.current.data).toBeUndefined()
      expect(mockedEquipmentService.listMachines).not.toHaveBeenCalled()
    })
  })

  describe('useMachine', () => {
    it('should fetch single machine by ID', async () => {
      const mockMachine = {
        id: 1,
        plant_id: 1,
        machine_code: 'MCH001',
        machine_name: 'CNC Machine 1',
        machine_type: 'CNC',
        status: 'RUNNING' as const,
        work_center_id: 1,
        capacity_per_hour: 100,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
      }

      mockedEquipmentService.getMachine.mockResolvedValue(mockMachine)

      const { result } = renderHook(() => useMachine(1), { wrapper: createWrapper() })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockMachine)
      expect(mockedEquipmentService.getMachine).toHaveBeenCalledWith(1)
    })

    it('should not fetch when ID is 0', async () => {
      const { result } = renderHook(() => useMachine(0), { wrapper: createWrapper() })

      expect(result.current.data).toBeUndefined()
      expect(mockedEquipmentService.getMachine).not.toHaveBeenCalled()
    })
  })

  describe('useOEEMetrics', () => {
    it('should fetch OEE metrics for a machine', async () => {
      const mockMetrics = {
        machine_id: 1,
        machine_name: 'CNC Machine 1',
        availability: 85.5,
        performance: 92.3,
        quality: 98.1,
        oee: 77.4,
        uptime_hours: 160,
        downtime_hours: 8,
        ideal_cycle_time: 30,
        actual_cycle_time: 32,
        good_parts: 4850,
        total_parts: 5000,
        calculated_at: '2024-01-08T00:00:00Z',
      }

      mockedEquipmentService.getOEEMetrics.mockResolvedValue(mockMetrics)

      const { result } = renderHook(() => useOEEMetrics(1), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockMetrics)
      expect(mockedEquipmentService.getOEEMetrics).toHaveBeenCalledWith(1, undefined, undefined)
    })

    it('should fetch OEE metrics with date range', async () => {
      const mockMetrics = {
        machine_id: 1,
        machine_name: 'CNC Machine 1',
        availability: 85.5,
        performance: 92.3,
        quality: 98.1,
        oee: 77.4,
        uptime_hours: 160,
        downtime_hours: 8,
        ideal_cycle_time: 30,
        actual_cycle_time: 32,
        good_parts: 4850,
        total_parts: 5000,
        calculated_at: '2024-01-08T00:00:00Z',
      }

      mockedEquipmentService.getOEEMetrics.mockResolvedValue(mockMetrics)

      const { result } = renderHook(
        () => useOEEMetrics(1, '2024-01-01', '2024-01-07'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(mockedEquipmentService.getOEEMetrics).toHaveBeenCalledWith(
        1,
        '2024-01-01',
        '2024-01-07'
      )
    })

    it('should not fetch when machineId is 0', async () => {
      const { result } = renderHook(() => useOEEMetrics(0), {
        wrapper: createWrapper(),
      })

      expect(result.current.data).toBeUndefined()
      expect(mockedEquipmentService.getOEEMetrics).not.toHaveBeenCalled()
    })
  })

  describe('useDowntimeHistory', () => {
    it('should fetch downtime history with default days', async () => {
      const mockDowntime = [
        {
          id: 1,
          machine_id: 1,
          start_time: '2024-01-01T08:00:00Z',
          end_time: '2024-01-01T10:00:00Z',
          duration_minutes: 120,
          category: 'BREAKDOWN',
          reason: 'Motor failure',
          notes: 'Replaced motor',
        },
      ]

      mockedEquipmentService.getDowntimeHistory.mockResolvedValue(mockDowntime)

      const { result } = renderHook(() => useDowntimeHistory(1), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockDowntime)
      expect(mockedEquipmentService.getDowntimeHistory).toHaveBeenCalledWith(1, 7)
    })

    it('should fetch downtime history with custom days', async () => {
      const mockDowntime = []

      mockedEquipmentService.getDowntimeHistory.mockResolvedValue(mockDowntime)

      const { result } = renderHook(() => useDowntimeHistory(1, 30), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(mockedEquipmentService.getDowntimeHistory).toHaveBeenCalledWith(1, 30)
    })
  })

  describe('useUpdateMachineStatus', () => {
    it('should update machine status', async () => {
      const mockUpdatedMachine = {
        id: 1,
        plant_id: 1,
        machine_code: 'MCH001',
        machine_name: 'CNC Machine 1',
        machine_type: 'CNC',
        status: 'MAINTENANCE' as const,
        work_center_id: 1,
        capacity_per_hour: 100,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-08T10:00:00Z',
      }

      mockedEquipmentService.updateMachineStatus.mockResolvedValue(mockUpdatedMachine)

      const { result } = renderHook(() => useUpdateMachineStatus(), {
        wrapper: createWrapper(),
      })

      await result.current.mutateAsync({ id: 1, status: 'MAINTENANCE' })

      expect(mockedEquipmentService.updateMachineStatus).toHaveBeenCalledWith(
        1,
        'MAINTENANCE'
      )
    })
  })
})
