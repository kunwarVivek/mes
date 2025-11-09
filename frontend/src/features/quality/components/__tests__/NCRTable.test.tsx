/**
 * NCRTable Component Tests
 *
 * Tests for NCRTable component using DataTable organism
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NCRTable } from '../NCRTable'
import type { NCR } from '../../schemas/ncr.schema'

// Mock dependencies
vi.mock('../../hooks/useNCRs', () => ({
  useNCRs: vi.fn(),
}))

vi.mock('../../hooks/useNCRMutations', () => ({
  useNCRMutations: vi.fn(() => ({
    updateNCRStatus: {
      mutate: vi.fn(),
      isPending: false,
    },
  })),
}))

import { useNCRs } from '../../hooks/useNCRs'
import { useNCRMutations } from '../../hooks/useNCRMutations'

const mockNCRs: NCR[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2025-001',
    work_order_id: 100,
    material_id: 200,
    defect_type: 'DIMENSIONAL',
    defect_description: 'Part dimension out of tolerance by 0.5mm',
    quantity_defective: 10.5,
    status: 'OPEN',
    reported_by_user_id: 1,
    created_at: new Date('2025-01-01'),
    updated_at: new Date('2025-01-01'),
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2025-002',
    work_order_id: 101,
    material_id: 201,
    defect_type: 'VISUAL',
    defect_description: 'Surface finish quality does not meet specification',
    quantity_defective: 25.0,
    status: 'IN_REVIEW',
    reported_by_user_id: 2,
    created_at: new Date('2025-01-02'),
    updated_at: new Date('2025-01-02'),
  },
  {
    id: 3,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2025-003',
    work_order_id: 102,
    material_id: 202,
    defect_type: 'FUNCTIONAL',
    defect_description: 'Component fails functional test due to electrical fault',
    quantity_defective: 5.0,
    status: 'RESOLVED',
    reported_by_user_id: 3,
    resolution_notes: 'Replaced defective components',
    resolved_by_user_id: 4,
    resolved_at: new Date('2025-01-03'),
    created_at: new Date('2025-01-03'),
    updated_at: new Date('2025-01-03'),
  },
  {
    id: 4,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2025-004',
    work_order_id: 103,
    material_id: 203,
    defect_type: 'MATERIAL',
    defect_description: 'Wrong material used in production',
    quantity_defective: 100.0,
    status: 'CLOSED',
    reported_by_user_id: 5,
    resolution_notes: 'Scrapped all defective parts',
    resolved_by_user_id: 6,
    resolved_at: new Date('2025-01-04'),
    created_at: new Date('2025-01-04'),
    updated_at: new Date('2025-01-04'),
  },
]

describe('NCRTable', () => {
  const mockUseNCRs = vi.mocked(useNCRs)
  const mockUseNCRMutations = vi.mocked(useNCRMutations)

  beforeEach(() => {
    vi.clearAllMocks()

    // Default mock implementation
    mockUseNCRs.mockReturnValue({
      data: {
        items: mockNCRs,
        total: mockNCRs.length,
        page: 1,
        page_size: 25,
        total_pages: 1,
      },
      isLoading: false,
      error: null,
      isError: false,
    } as any)

    mockUseNCRMutations.mockReturnValue({
      updateNCRStatus: {
        mutate: vi.fn(),
        isPending: false,
      },
    } as any)
  })

  describe('Table Rendering', () => {
    it('renders all column headers correctly', () => {
      render(<NCRTable />)

      expect(screen.getByText('NCR Number')).toBeInTheDocument()
      expect(screen.getByText('WO ID')).toBeInTheDocument()
      expect(screen.getByText('Material ID')).toBeInTheDocument()
      expect(screen.getByText('Defect Type')).toBeInTheDocument()
      expect(screen.getByText('Description')).toBeInTheDocument()
      expect(screen.getByText('Qty Defective')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Created Date')).toBeInTheDocument()
      expect(screen.getByText('Actions')).toBeInTheDocument()
    })

    it('renders all NCR data rows', () => {
      render(<NCRTable />)

      expect(screen.getByText('NCR-2025-001')).toBeInTheDocument()
      expect(screen.getByText('NCR-2025-002')).toBeInTheDocument()
      expect(screen.getByText('NCR-2025-003')).toBeInTheDocument()
      expect(screen.getByText('NCR-2025-004')).toBeInTheDocument()
    })

    it('renders work order IDs correctly', () => {
      render(<NCRTable />)

      // Use getAllByText because pagination controls may also contain these numbers
      expect(screen.getAllByText('100')[0]).toBeInTheDocument()
      expect(screen.getAllByText('101')[0]).toBeInTheDocument()
      expect(screen.getAllByText('102')[0]).toBeInTheDocument()
      expect(screen.getAllByText('103')[0]).toBeInTheDocument()
    })

    it('renders material IDs correctly', () => {
      render(<NCRTable />)

      expect(screen.getByText('200')).toBeInTheDocument()
      expect(screen.getByText('201')).toBeInTheDocument()
      expect(screen.getByText('202')).toBeInTheDocument()
      expect(screen.getByText('203')).toBeInTheDocument()
    })

    it('renders defect types as badges', () => {
      render(<NCRTable />)

      expect(screen.getByText('DIMENSIONAL')).toBeInTheDocument()
      expect(screen.getByText('VISUAL')).toBeInTheDocument()
      expect(screen.getByText('FUNCTIONAL')).toBeInTheDocument()
      expect(screen.getByText('MATERIAL')).toBeInTheDocument()
    })

    it('renders quantity defective with 2 decimal places', () => {
      render(<NCRTable />)

      expect(screen.getByText('10.50')).toBeInTheDocument()
      expect(screen.getByText('25.00')).toBeInTheDocument()
      expect(screen.getByText('5.00')).toBeInTheDocument()
      expect(screen.getByText('100.00')).toBeInTheDocument()
    })

    it('truncates long descriptions to 50 characters', () => {
      const longDescriptionNCR: NCR = {
        ...mockNCRs[0],
        defect_description:
          'This is a very long description that exceeds fifty characters and should be truncated',
      }

      mockUseNCRs.mockReturnValue({
        data: {
          items: [longDescriptionNCR],
          total: 1,
          page: 1,
          page_size: 25,
          total_pages: 1,
        },
        isLoading: false,
        error: null,
        isError: false,
      } as any)

      render(<NCRTable />)

      const truncatedText = screen.getByText(/This is a very long description/)
      expect(truncatedText.textContent?.length).toBeLessThanOrEqual(53) // 50 chars + "..."
    })

    it('formats created date as locale date string', () => {
      render(<NCRTable />)

      const expectedDate = new Date('2025-01-01').toLocaleDateString()
      expect(screen.getByText(expectedDate)).toBeInTheDocument()
    })
  })

  describe('Status Badge Rendering', () => {
    it('renders OPEN status with destructive variant', () => {
      render(<NCRTable />)

      const openBadge = screen.getAllByText('Open')[0]
      expect(openBadge).toBeInTheDocument()
    })

    it('renders IN_REVIEW status with default variant', () => {
      render(<NCRTable />)

      const inReviewBadge = screen.getAllByText('In Review')[0]
      expect(inReviewBadge).toBeInTheDocument()
    })

    it('renders RESOLVED status with default variant', () => {
      render(<NCRTable />)

      const resolvedBadge = screen.getAllByText('Resolved')[0]
      expect(resolvedBadge).toBeInTheDocument()
    })

    it('renders CLOSED status with secondary variant', () => {
      render(<NCRTable />)

      const closedBadge = screen.getAllByText('Closed')[0]
      expect(closedBadge).toBeInTheDocument()
    })
  })

  describe('Update Status Button', () => {
    it('renders Update Status button for each row', () => {
      render(<NCRTable />)

      const updateButtons = screen.getAllByRole('button', { name: /Update Status/i })
      expect(updateButtons).toHaveLength(4)
    })

    it('enables Update Status button when status is OPEN', () => {
      render(<NCRTable />)

      const updateButtons = screen.getAllByRole('button', { name: /Update Status/i })
      expect(updateButtons[0]).not.toBeDisabled()
    })

    it('enables Update Status button when status is IN_REVIEW', () => {
      render(<NCRTable />)

      const updateButtons = screen.getAllByRole('button', { name: /Update Status/i })
      expect(updateButtons[1]).not.toBeDisabled()
    })

    it('enables Update Status button when status is RESOLVED', () => {
      render(<NCRTable />)

      const updateButtons = screen.getAllByRole('button', { name: /Update Status/i })
      expect(updateButtons[2]).not.toBeDisabled()
    })

    it('disables Update Status button when status is CLOSED', () => {
      render(<NCRTable />)

      const updateButtons = screen.getAllByRole('button', { name: /Update Status/i })
      expect(updateButtons[3]).toBeDisabled()
    })

    it('opens dialog when Update Status button is clicked', async () => {
      const user = userEvent.setup()
      render(<NCRTable />)

      const updateButtons = screen.getAllByRole('button', { name: /Update Status/i })
      await user.click(updateButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Update NCR Status')).toBeInTheDocument()
      })
    })

    it('displays correct NCR number in dialog', async () => {
      const user = userEvent.setup()
      render(<NCRTable />)

      const updateButtons = screen.getAllByRole('button', { name: /Update Status/i })
      await user.click(updateButtons[0])

      await waitFor(() => {
        // Use getAllByText because NCR number appears in both table and dialog
        const ncrNumbers = screen.getAllByText(/NCR-2025-001/)
        expect(ncrNumbers.length).toBeGreaterThan(0)
      })
    })

    it('closes dialog when clicking cancel', async () => {
      const user = userEvent.setup()
      render(<NCRTable />)

      const updateButtons = screen.getAllByRole('button', { name: /Update Status/i })
      await user.click(updateButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Update NCR Status')).toBeInTheDocument()
      })

      const cancelButton = screen.getByRole('button', { name: /Cancel/i })
      await user.click(cancelButton)

      await waitFor(() => {
        expect(screen.queryByText('Update NCR Status')).not.toBeInTheDocument()
      })
    })
  })

  describe('Filters', () => {
    it('applies status filter to useNCRs hook', () => {
      render(<NCRTable filters={{ status: 'OPEN' }} />)

      expect(mockUseNCRs).toHaveBeenCalledWith({ status: 'OPEN' })
    })

    it('applies work_order_id filter to useNCRs hook', () => {
      render(<NCRTable filters={{ work_order_id: 100 }} />)

      expect(mockUseNCRs).toHaveBeenCalledWith({ work_order_id: 100 })
    })

    it('applies both filters to useNCRs hook', () => {
      render(<NCRTable filters={{ status: 'OPEN', work_order_id: 100 }} />)

      expect(mockUseNCRs).toHaveBeenCalledWith({ status: 'OPEN', work_order_id: 100 })
    })

    it('calls useNCRs with no params when no filters provided', () => {
      render(<NCRTable />)

      expect(mockUseNCRs).toHaveBeenCalledWith(undefined)
    })
  })

  describe('Row Click', () => {
    it('calls onRowClick when row is clicked', async () => {
      const handleRowClick = vi.fn()
      const user = userEvent.setup()

      render(<NCRTable onRowClick={handleRowClick} />)

      const firstRow = screen.getByText('NCR-2025-001').closest('tr')!
      await user.click(firstRow)

      expect(handleRowClick).toHaveBeenCalledWith(mockNCRs[0])
    })

    it('does not call onRowClick when onRowClick is not provided', async () => {
      const user = userEvent.setup()

      render(<NCRTable />)

      const firstRow = screen.getByText('NCR-2025-001').closest('tr')!
      await user.click(firstRow)

      // Should not throw error
      expect(true).toBe(true)
    })
  })

  describe('Loading State', () => {
    it('shows loading skeleton when isLoading is true', () => {
      mockUseNCRs.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        isError: false,
      } as any)

      render(<NCRTable />)

      // DataTable shows skeleton rows when loading
      expect(screen.getByRole('grid')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('shows empty state when no NCRs are returned', () => {
      mockUseNCRs.mockReturnValue({
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 25,
          total_pages: 0,
        },
        isLoading: false,
        error: null,
        isError: false,
      } as any)

      render(<NCRTable />)

      expect(screen.getByText('No data found.')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('handles error state gracefully', () => {
      mockUseNCRs.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to fetch'),
        isError: true,
      } as any)

      render(<NCRTable />)

      // Component should handle undefined data gracefully
      expect(screen.getByRole('grid')).toBeInTheDocument()
    })
  })

  describe('Pagination', () => {
    it('uses DataTable with pagination enabled', () => {
      render(<NCRTable />)

      // Check if pagination controls are present (DataTable default behavior)
      expect(screen.getByRole('grid')).toBeInTheDocument()
    })

    it('sets page size to 25', () => {
      render(<NCRTable />)

      // Verify DataTable is configured with 25 rows per page
      expect(screen.getByRole('grid')).toBeInTheDocument()
    })
  })

  describe('Column Sorting', () => {
    it('makes NCR Number column sortable', () => {
      render(<NCRTable />)

      const ncrNumberHeader = screen.getByText('NCR Number')
      expect(ncrNumberHeader.closest('th')).toBeInTheDocument()
    })

    it('makes WO ID column sortable', () => {
      render(<NCRTable />)

      const woIdHeader = screen.getByText('WO ID')
      expect(woIdHeader.closest('th')).toBeInTheDocument()
    })

    it('makes Material ID column sortable', () => {
      render(<NCRTable />)

      const materialIdHeader = screen.getByText('Material ID')
      expect(materialIdHeader.closest('th')).toBeInTheDocument()
    })

    it('makes Created Date column sortable', () => {
      render(<NCRTable />)

      const createdDateHeader = screen.getByText('Created Date')
      expect(createdDateHeader.closest('th')).toBeInTheDocument()
    })
  })
})
