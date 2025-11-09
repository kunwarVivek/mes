/**
 * Tests for useNCRMutations Hook
 *
 * Testing that API error details are displayed in toast notifications
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useNCRMutations } from '../useNCRMutations'
import { ncrService } from '../../services/ncr.service'
import { useToast } from '@/components/ui/use-toast'

// Mock dependencies
vi.mock('../../services/ncr.service')

vi.mock('@/components/ui/use-toast', () => ({
  useToast: vi.fn(() => ({ toast: vi.fn() })),
  toast: vi.fn(),
}))

describe('useNCRMutations - Error Detail Display', () => {
  let queryClient: QueryClient
  const mockToast = vi.fn()

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
    vi.mocked(useToast).mockReturnValue({ toast: mockToast })
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('createNCR error handling', () => {
    it('should display API error details in toast when available', async () => {
      const apiError = {
        response: {
          data: {
            detail: 'NCR number already exists in system',
          },
        },
      }

      vi.mocked(ncrService.create).mockRejectedValue(apiError)

      const { result } = renderHook(() => useNCRMutations(), { wrapper })

      result.current.createNCR.mutate({
        ncr_number: 'NCR-001',
        description: 'Test NCR',
        status: 'OPEN',
        priority: 'HIGH',
        root_cause: 'Material defect',
        corrective_action: 'Replace material',
      })

      await waitFor(() => expect(result.current.createNCR.isError).toBe(true))

      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Error',
          description: 'NCR number already exists in system',
          variant: 'destructive',
        })
      )
    })

    it('should display generic error message when API detail not available', async () => {
      const apiError = new Error('Network error')

      vi.mocked(ncrService.create).mockRejectedValue(apiError)

      const { result } = renderHook(() => useNCRMutations(), { wrapper })

      result.current.createNCR.mutate({
        ncr_number: 'NCR-001',
        description: 'Test NCR',
        status: 'OPEN',
        priority: 'HIGH',
        root_cause: 'Material defect',
        corrective_action: 'Replace material',
      })

      await waitFor(() => expect(result.current.createNCR.isError).toBe(true))

      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Error',
          description: 'Failed to create NCR',
          variant: 'destructive',
        })
      )
    })
  })

  describe('updateNCRStatus error handling', () => {
    it('should display API error details in toast when available', async () => {
      const apiError = {
        response: {
          data: {
            detail: 'NCR status transition invalid: Cannot resolve CLOSED NCR',
          },
        },
      }

      vi.mocked(ncrService.updateStatus).mockRejectedValue(apiError)

      const { result } = renderHook(() => useNCRMutations(), { wrapper })

      result.current.updateNCRStatus.mutate({
        id: 1,
        data: { status: 'RESOLVED' },
      })

      await waitFor(() => expect(result.current.updateNCRStatus.isError).toBe(true))

      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Error',
          description: 'NCR status transition invalid: Cannot resolve CLOSED NCR',
          variant: 'destructive',
        })
      )
    })

    it('should display generic error message when API detail not available', async () => {
      const apiError = new Error('Network error')

      vi.mocked(ncrService.updateStatus).mockRejectedValue(apiError)

      const { result } = renderHook(() => useNCRMutations(), { wrapper })

      result.current.updateNCRStatus.mutate({
        id: 1,
        data: { status: 'RESOLVED' },
      })

      await waitFor(() => expect(result.current.updateNCRStatus.isError).toBe(true))

      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Error',
          description: 'Failed to update NCR status',
          variant: 'destructive',
        })
      )
    })
  })
})
