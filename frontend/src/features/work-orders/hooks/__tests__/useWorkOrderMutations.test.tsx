import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWorkOrderMutations } from '../useWorkOrderMutations'
import { workOrderService } from '../../services/work-order.service'
import { toast } from '@/components/ui/use-toast'

vi.mock('../../services/work-order.service')
vi.mock('@/components/ui/use-toast')

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

describe('useWorkOrderMutations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createWorkOrder', () => {
    it('calls service and shows success toast', async () => {
      const mockWorkOrder = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'PLANNED',
      }

      vi.mocked(workOrderService.create).mockResolvedValue(mockWorkOrder as any)

      const { result } = renderHook(() => useWorkOrderMutations(), {
        wrapper: createWrapper(),
      })

      const createData = {
        material_id: 1,
        order_type: 'PRODUCTION' as const,
        planned_quantity: 100,
        priority: 5,
      }

      result.current.createWorkOrder.mutate(createData)

      await waitFor(() => {
        expect(result.current.createWorkOrder.isSuccess).toBe(true)
      })

      expect(workOrderService.create).toHaveBeenCalledWith(createData)
      expect(toast).toHaveBeenCalledWith({
        title: 'Work order created successfully',
      })
    })

    it('shows error toast on failure', async () => {
      const error = {
        response: {
          data: {
            detail: 'Material not found',
          },
        },
      }

      vi.mocked(workOrderService.create).mockRejectedValue(error)

      const { result } = renderHook(() => useWorkOrderMutations(), {
        wrapper: createWrapper(),
      })

      const createData = {
        material_id: 999,
        order_type: 'PRODUCTION' as const,
        planned_quantity: 100,
        priority: 5,
      }

      result.current.createWorkOrder.mutate(createData)

      await waitFor(() => {
        expect(result.current.createWorkOrder.isError).toBe(true)
      })

      expect(toast).toHaveBeenCalledWith({
        title: 'Failed to create work order',
        description: 'Material not found',
        variant: 'destructive',
      })
    })
  })

  describe('updateWorkOrder', () => {
    it('calls service and shows success toast', async () => {
      const mockWorkOrder = {
        id: 1,
        work_order_number: 'WO-2025-001',
        planned_quantity: 150,
      }

      vi.mocked(workOrderService.update).mockResolvedValue(mockWorkOrder as any)

      const { result } = renderHook(() => useWorkOrderMutations(), {
        wrapper: createWrapper(),
      })

      const updateData = {
        id: 1,
        data: {
          planned_quantity: 150,
        },
      }

      result.current.updateWorkOrder.mutate(updateData)

      await waitFor(() => {
        expect(result.current.updateWorkOrder.isSuccess).toBe(true)
      })

      expect(workOrderService.update).toHaveBeenCalledWith(1, { planned_quantity: 150 })
      expect(toast).toHaveBeenCalledWith({
        title: 'Work order updated successfully',
      })
    })
  })

  describe('cancelWorkOrder', () => {
    it('calls service and shows success toast', async () => {
      const mockWorkOrder = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'CANCELLED',
      }

      vi.mocked(workOrderService.cancel).mockResolvedValue(mockWorkOrder as any)

      const { result } = renderHook(() => useWorkOrderMutations(), {
        wrapper: createWrapper(),
      })

      result.current.cancelWorkOrder.mutate(1)

      await waitFor(() => {
        expect(result.current.cancelWorkOrder.isSuccess).toBe(true)
      })

      expect(workOrderService.cancel).toHaveBeenCalledWith(1)
      expect(toast).toHaveBeenCalledWith({
        title: 'Work order cancelled successfully',
      })
    })
  })

  describe('releaseWorkOrder', () => {
    it('calls service and shows success toast for state transition', async () => {
      const mockWorkOrder = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'RELEASED',
      }

      vi.mocked(workOrderService.release).mockResolvedValue(mockWorkOrder as any)

      const { result } = renderHook(() => useWorkOrderMutations(), {
        wrapper: createWrapper(),
      })

      result.current.releaseWorkOrder.mutate(1)

      await waitFor(() => {
        expect(result.current.releaseWorkOrder.isSuccess).toBe(true)
      })

      expect(workOrderService.release).toHaveBeenCalledWith(1)
      expect(toast).toHaveBeenCalledWith({
        title: 'Work order released successfully',
      })
    })

    it('shows error toast when invalid state transition', async () => {
      const error = {
        response: {
          data: {
            detail: 'Cannot release work order from COMPLETED status',
          },
        },
      }

      vi.mocked(workOrderService.release).mockRejectedValue(error)

      const { result } = renderHook(() => useWorkOrderMutations(), {
        wrapper: createWrapper(),
      })

      result.current.releaseWorkOrder.mutate(1)

      await waitFor(() => {
        expect(result.current.releaseWorkOrder.isError).toBe(true)
      })

      expect(toast).toHaveBeenCalledWith({
        title: 'Failed to release work order',
        description: 'Cannot release work order from COMPLETED status',
        variant: 'destructive',
      })
    })
  })

  describe('startWorkOrder', () => {
    it('calls service and shows success toast for state transition', async () => {
      const mockWorkOrder = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'IN_PROGRESS',
      }

      vi.mocked(workOrderService.start).mockResolvedValue(mockWorkOrder as any)

      const { result } = renderHook(() => useWorkOrderMutations(), {
        wrapper: createWrapper(),
      })

      result.current.startWorkOrder.mutate(1)

      await waitFor(() => {
        expect(result.current.startWorkOrder.isSuccess).toBe(true)
      })

      expect(workOrderService.start).toHaveBeenCalledWith(1)
      expect(toast).toHaveBeenCalledWith({
        title: 'Work order started successfully',
      })
    })
  })

  describe('completeWorkOrder', () => {
    it('calls service and shows success toast for state transition', async () => {
      const mockWorkOrder = {
        id: 1,
        work_order_number: 'WO-2025-001',
        order_status: 'COMPLETED',
      }

      vi.mocked(workOrderService.complete).mockResolvedValue(mockWorkOrder as any)

      const { result } = renderHook(() => useWorkOrderMutations(), {
        wrapper: createWrapper(),
      })

      result.current.completeWorkOrder.mutate(1)

      await waitFor(() => {
        expect(result.current.completeWorkOrder.isSuccess).toBe(true)
      })

      expect(workOrderService.complete).toHaveBeenCalledWith(1)
      expect(toast).toHaveBeenCalledWith({
        title: 'Work order completed successfully',
      })
    })
  })
})
