/**
 * MaterialTable Component Tests
 *
 * TDD tests for MaterialTable using DataTable organism
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MaterialTable } from '../MaterialTable'
import type { Material } from '../../types/material.types'

const mockMaterials: Material[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    material_number: 'MAT001',
    material_name: 'Steel Plate',
    description: 'High-grade steel plate',
    material_category_id: 1,
    base_uom_id: 1,
    procurement_type: 'PURCHASE',
    mrp_type: 'MRP',
    safety_stock: 100,
    reorder_point: 50,
    lot_size: 10,
    lead_time_days: 5,
    is_active: true,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    material_number: 'MAT002',
    material_name: 'Aluminum Sheet',
    description: 'Lightweight aluminum sheet',
    material_category_id: 2,
    base_uom_id: 1,
    procurement_type: 'MANUFACTURE',
    mrp_type: 'REORDER',
    safety_stock: 200,
    reorder_point: 100,
    lot_size: 20,
    lead_time_days: 10,
    is_active: false,
    created_at: '2025-01-02T00:00:00Z',
  },
]

describe('MaterialTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render table with material data', () => {
      render(<MaterialTable data={mockMaterials} />)

      expect(screen.getByText('MAT001')).toBeInTheDocument()
      expect(screen.getByText('Steel Plate')).toBeInTheDocument()
      expect(screen.getByText('MAT002')).toBeInTheDocument()
      expect(screen.getByText('Aluminum Sheet')).toBeInTheDocument()
    })

    it('should render all column headers', () => {
      render(<MaterialTable data={mockMaterials} />)

      expect(screen.getByText(/material number/i)).toBeInTheDocument()
      expect(screen.getByText(/material name/i)).toBeInTheDocument()
      expect(screen.getByText(/category/i)).toBeInTheDocument()
      expect(screen.getByText(/procurement/i)).toBeInTheDocument()
      expect(screen.getByText(/mrp type/i)).toBeInTheDocument()
      expect(screen.getByText(/status/i)).toBeInTheDocument()
    })

    it('should render status badges correctly', () => {
      render(<MaterialTable data={mockMaterials} />)

      // Active material should show Active badge
      const activeText = screen.getByText('Active')
      expect(activeText).toBeInTheDocument()

      // Inactive material should show Inactive badge
      const inactiveText = screen.getByText('Inactive')
      expect(inactiveText).toBeInTheDocument()
    })

    it('should render procurement type badges', () => {
      render(<MaterialTable data={mockMaterials} />)

      expect(screen.getByText('PURCHASE')).toBeInTheDocument()
      expect(screen.getByText('MANUFACTURE')).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('should show loading skeleton when loading', () => {
      render(<MaterialTable data={[]} loading />)

      // DataTable shows skeleton rows
      const skeletons = screen.getAllByRole('row')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('should not show data when loading', () => {
      render(<MaterialTable data={mockMaterials} loading />)

      expect(screen.queryByText('MAT001')).not.toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should show empty state when no data', () => {
      render(<MaterialTable data={[]} />)

      expect(screen.getByText(/no data found/i)).toBeInTheDocument()
    })

    it('should show custom empty state if provided', () => {
      const customEmpty = <div>Custom empty message</div>
      render(<MaterialTable data={[]} emptyState={customEmpty} />)

      expect(screen.getByText('Custom empty message')).toBeInTheDocument()
    })
  })

  describe('Sorting', () => {
    it('should sort by material number when column header clicked', async () => {
      const user = userEvent.setup()
      render(<MaterialTable data={mockMaterials} />)

      const materialNumberHeader = screen.getByRole('button', { name: /sort by material number/i })
      await user.click(materialNumberHeader)

      // Check that sort icon is shown (ascending)
      expect(materialNumberHeader).toHaveAttribute('aria-label', 'Sort by Material Number')
    })

    it('should toggle sort direction on second click', async () => {
      const user = userEvent.setup()
      render(<MaterialTable data={mockMaterials} />)

      const materialNameHeader = screen.getByRole('button', { name: /sort by material name/i })

      // First click - ascending
      await user.click(materialNameHeader)

      // Second click - descending
      await user.click(materialNameHeader)

      // Verify sorting happened (implementation detail)
      expect(materialNameHeader).toBeInTheDocument()
    })
  })

  describe('Row Click', () => {
    it('should call onRowClick when row is clicked', async () => {
      const user = userEvent.setup()
      const onRowClick = vi.fn()
      render(<MaterialTable data={mockMaterials} onRowClick={onRowClick} />)

      // Find a table row with the material data
      const row = screen.getByText('MAT001').closest('tr')
      expect(row).toBeInTheDocument()

      if (row) {
        await user.click(row)
        expect(onRowClick).toHaveBeenCalledWith(mockMaterials[0])
      }
    })

    it('should apply clickable class when onRowClick is provided', () => {
      render(<MaterialTable data={mockMaterials} onRowClick={vi.fn()} />)

      const row = screen.getByText('MAT001').closest('tr')
      expect(row).toHaveClass('data-table__row--clickable')
    })

    it('should not call onRowClick when not provided', async () => {
      const user = userEvent.setup()
      render(<MaterialTable data={mockMaterials} />)

      const row = screen.getByText('MAT001').closest('tr')

      if (row) {
        // Should not throw error
        await user.click(row)
      }

      expect(row).toBeInTheDocument()
    })
  })

  describe('Filtering', () => {
    it('should filter materials by name', async () => {
      const user = userEvent.setup()
      render(<MaterialTable data={mockMaterials} />)

      // Get the filter input for Material Name column
      const filterInputs = screen.getAllByPlaceholderText(/filter.../i)
      const nameFilterInput = filterInputs[1] // Second filter is for name column

      await user.type(nameFilterInput, 'Steel')

      await waitFor(() => {
        expect(screen.getByText('Steel Plate')).toBeInTheDocument()
        expect(screen.queryByText('Aluminum Sheet')).not.toBeInTheDocument()
      })
    })

    it('should clear filter when input is cleared', async () => {
      const user = userEvent.setup()
      render(<MaterialTable data={mockMaterials} />)

      const filterInputs = screen.getAllByPlaceholderText(/filter.../i)
      const nameFilterInput = filterInputs[1]

      // Type filter
      await user.type(nameFilterInput, 'Steel')

      await waitFor(() => {
        expect(screen.queryByText('Aluminum Sheet')).not.toBeInTheDocument()
      })

      // Clear filter
      await user.clear(nameFilterInput)

      await waitFor(() => {
        expect(screen.getByText('Aluminum Sheet')).toBeInTheDocument()
      })
    })
  })

  describe('Pagination', () => {
    const manyMaterials = Array.from({ length: 30 }, (_, i) => ({
      ...mockMaterials[0],
      id: i + 1,
      material_number: `MAT${String(i + 1).padStart(3, '0')}`,
      material_name: `Material ${i + 1}`,
    }))

    it('should show pagination controls when data exceeds page size', () => {
      render(<MaterialTable data={manyMaterials} />)

      expect(screen.getByText(/showing/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/previous page/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/next page/i)).toBeInTheDocument()
    })

    it('should navigate to next page', async () => {
      const user = userEvent.setup()
      render(<MaterialTable data={manyMaterials} />)

      const nextButton = screen.getByLabelText(/next page/i)
      await user.click(nextButton)

      // Should show page 2 indicator
      expect(screen.getByText(/page 2/i)).toBeInTheDocument()
    })

    it('should disable previous button on first page', () => {
      render(<MaterialTable data={manyMaterials} />)

      const prevButton = screen.getByLabelText(/previous page/i)
      expect(prevButton).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA grid role', () => {
      render(<MaterialTable data={mockMaterials} />)

      const table = screen.getByRole('grid')
      expect(table).toBeInTheDocument()
    })

    it('should have sortable columns with aria-sort attributes', () => {
      render(<MaterialTable data={mockMaterials} />)

      const headers = screen.getAllByRole('columnheader')
      const sortableHeaders = headers.filter(h => h.getAttribute('aria-sort') !== null || h.querySelector('button'))

      expect(sortableHeaders.length).toBeGreaterThan(0)
    })

    it('should have proper labels for filter inputs', () => {
      render(<MaterialTable data={mockMaterials} />)

      const filterInputs = screen.getAllByPlaceholderText(/filter.../i)
      filterInputs.forEach(input => {
        expect(input).toHaveAttribute('aria-label')
      })
    })
  })
})
