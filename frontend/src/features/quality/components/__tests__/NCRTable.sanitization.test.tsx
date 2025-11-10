/**
 * NCRTable Sanitization Tests
 *
 * Tests to verify XSS prevention in NCRTable component
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NCRTable } from '../NCRTable'
import type { NCR } from '../../schemas/ncr.schema'

// Mock the hooks
vi.mock('../../hooks/useNCRs', () => ({
  useNCRs: () => ({
    data: {
      items: [
        {
          id: 1,
          ncr_number: 'NCR-2025-001',
          work_order_id: 100,
          material_id: 200,
          defect_type: 'DIMENSIONAL',
          defect_description: '<script>alert("XSS")</script>Critical defect found',
          quantity_defective: 5.0,
          status: 'OPEN',
          created_at: new Date('2025-01-01'),
          reported_by_user_id: 1,
        },
        {
          id: 2,
          ncr_number: 'NCR-2025-002',
          work_order_id: 101,
          material_id: 201,
          defect_type: 'VISUAL',
          defect_description: '<img src="x" onerror="alert(\'XSS\')">Surface damage',
          quantity_defective: 10.0,
          status: 'IN_REVIEW',
          created_at: new Date('2025-01-02'),
          reported_by_user_id: 2,
        },
      ] as NCR[],
    },
    isLoading: false,
  }),
}))

describe('NCRTable - XSS Prevention', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('should sanitize script tags in defect descriptions', () => {
    render(<NCRTable />, { wrapper })

    // The script tag should be removed (table has role="grid" in DataTable component)
    const tableContent = screen.getByRole('grid')
    expect(tableContent.innerHTML).not.toContain('<script>')
    expect(tableContent.innerHTML).not.toContain('alert("XSS")')

    // But the safe content should remain
    expect(tableContent.innerHTML).toContain('Critical defect found')
  })

  it('should sanitize event handlers in defect descriptions', () => {
    render(<NCRTable />, { wrapper })

    const tableContent = screen.getByRole('grid')
    expect(tableContent.innerHTML).not.toContain('onerror')
    expect(tableContent.innerHTML).not.toContain('alert(\'XSS\')')

    // Safe content should remain
    expect(tableContent.innerHTML).toContain('Surface damage')
  })

  it('should display NCR numbers without sanitization (safe data)', () => {
    render(<NCRTable />, { wrapper })

    expect(screen.getByText('NCR-2025-001')).toBeInTheDocument()
    expect(screen.getByText('NCR-2025-002')).toBeInTheDocument()
  })

  it('should not execute any JavaScript from user content', () => {
    // Mock console.error to catch any XSS attempts
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    render(<NCRTable />, { wrapper })

    // No alerts should be triggered
    expect(alertSpy).not.toHaveBeenCalled()

    consoleError.mockRestore()
    alertSpy.mockRestore()
  })
})
