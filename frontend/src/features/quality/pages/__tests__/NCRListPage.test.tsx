/**
 * NCRListPage Component Tests
 *
 * Tests for NCRListPage with search, filters, and navigation
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NCRListPage } from '../NCRListPage'
import type { NCR } from '../../schemas/ncr.schema'

// Mock dependencies
vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
}))

vi.mock('../../hooks/useNCRs', () => ({
  useNCRs: vi.fn(),
}))

vi.mock('../../components/NCRTable', () => ({
  NCRTable: vi.fn(({ filters, onRowClick }) => (
    <div data-testid="ncr-table">
      <div data-testid="filters">{JSON.stringify(filters)}</div>
      <button onClick={() => onRowClick?.({ id: 1 })}>Mock Row Click</button>
    </div>
  )),
}))

import { useNavigate } from 'react-router-dom'
import { useNCRs } from '../../hooks/useNCRs'
import { NCRTable } from '../../components/NCRTable'

const mockNCRs: NCR[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2025-001',
    work_order_id: 100,
    material_id: 200,
    defect_type: 'DIMENSIONAL',
    defect_description: 'Part dimension out of tolerance',
    quantity_defective: 10.5,
    status: 'OPEN',
    reported_by_user_id: 1,
    created_at: new Date('2025-01-01'),
    updated_at: new Date('2025-01-01'),
  },
]

describe('NCRListPage', () => {
  const mockNavigate = vi.fn()
  const mockUseNCRs = vi.mocked(useNCRs)

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)

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
  })

  describe('Page Layout', () => {
    it('renders page title', () => {
      render(<NCRListPage />)

      expect(screen.getByText('Non-Conformance Reports')).toBeInTheDocument()
    })

    it('renders Create NCR button', () => {
      render(<NCRListPage />)

      expect(screen.getByRole('button', { name: /Create NCR/i })).toBeInTheDocument()
    })

    it('renders search input', () => {
      render(<NCRListPage />)

      expect(screen.getByPlaceholderText(/Search NCR/i)).toBeInTheDocument()
    })

    it('renders status filter dropdown', () => {
      render(<NCRListPage />)

      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('renders NCRTable component', () => {
      render(<NCRListPage />)

      expect(screen.getByTestId('ncr-table')).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    it('updates search query on input change', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const searchInput = screen.getByPlaceholderText(/Search NCR/i)
      await user.type(searchInput, 'NCR-2025-001')

      expect(searchInput).toHaveValue('NCR-2025-001')
    })

    it('clears search input when clear button is clicked', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const searchInput = screen.getByPlaceholderText(/Search NCR/i)
      await user.type(searchInput, 'NCR-2025-001')

      const clearButton = screen.getByRole('button', { name: /clear/i })
      await user.click(clearButton)

      expect(searchInput).toHaveValue('')
    })
  })

  describe('Status Filter', () => {
    it('shows All option in status filter', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const statusFilter = screen.getByRole('combobox')
      await user.click(statusFilter)

      expect(screen.getByRole('option', { name: /All/i })).toBeInTheDocument()
    })

    it('shows OPEN option in status filter', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const statusFilter = screen.getByRole('combobox')
      await user.click(statusFilter)

      expect(screen.getByRole('option', { name: /Open/i })).toBeInTheDocument()
    })

    it('shows IN_REVIEW option in status filter', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const statusFilter = screen.getByRole('combobox')
      await user.click(statusFilter)

      expect(screen.getByRole('option', { name: /In Review/i })).toBeInTheDocument()
    })

    it('shows RESOLVED option in status filter', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const statusFilter = screen.getByRole('combobox')
      await user.click(statusFilter)

      expect(screen.getByRole('option', { name: /Resolved/i })).toBeInTheDocument()
    })

    it('shows CLOSED option in status filter', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const statusFilter = screen.getByRole('combobox')
      await user.click(statusFilter)

      expect(screen.getByRole('option', { name: /Closed/i })).toBeInTheDocument()
    })

    it('updates status filter on selection change', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const statusFilter = screen.getByRole('combobox')
      await user.click(statusFilter)

      const openOption = screen.getByRole('option', { name: /Open/i })
      await user.click(openOption)

      // Verify filter is applied (check via NCRTable mock)
      await waitFor(() => {
        const filtersDiv = screen.getByTestId('filters')
        expect(filtersDiv.textContent).toContain('OPEN')
      })
    })

    it('clears status filter when All is selected', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const statusFilter = screen.getByRole('combobox')

      // First select OPEN
      await user.click(statusFilter)
      await user.click(screen.getByRole('option', { name: /Open/i }))

      // Then select All
      await user.click(statusFilter)
      await user.click(screen.getByRole('option', { name: /All/i }))

      await waitFor(() => {
        const filtersDiv = screen.getByTestId('filters')
        expect(filtersDiv.textContent).not.toContain('OPEN')
      })
    })
  })

  describe('Filter Passing to NCRTable', () => {
    it('passes no filters initially', () => {
      render(<NCRListPage />)

      const filtersDiv = screen.getByTestId('filters')
      // When no filters, NCRTable receives undefined (which JSON.stringify converts to empty string)
      expect(filtersDiv.textContent).toBe('')
    })

    it('passes search query filter to NCRTable', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const searchInput = screen.getByPlaceholderText(/Search NCR/i)
      await user.type(searchInput, 'NCR-2025-001')

      await waitFor(() => {
        const filtersDiv = screen.getByTestId('filters')
        expect(filtersDiv.textContent).toContain('NCR-2025-001')
      })
    })

    it('passes status filter to NCRTable', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const statusFilter = screen.getByRole('combobox')
      await user.click(statusFilter)
      await user.click(screen.getByRole('option', { name: /Open/i }))

      await waitFor(() => {
        const filtersDiv = screen.getByTestId('filters')
        expect(filtersDiv.textContent).toContain('OPEN')
      })
    })

    it('passes both filters to NCRTable', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const searchInput = screen.getByPlaceholderText(/Search NCR/i)
      await user.type(searchInput, 'NCR-2025')

      const statusFilter = screen.getByRole('combobox')
      await user.click(statusFilter)
      await user.click(screen.getByRole('option', { name: /Open/i }))

      await waitFor(() => {
        const filtersDiv = screen.getByTestId('filters')
        expect(filtersDiv.textContent).toContain('NCR-2025')
        expect(filtersDiv.textContent).toContain('OPEN')
      })
    })
  })

  describe('Navigation', () => {
    it('navigates to create page on Create NCR button click', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const createButton = screen.getByRole('button', { name: /Create NCR/i })
      await user.click(createButton)

      expect(mockNavigate).toHaveBeenCalledWith('/quality/ncrs/new')
    })

    it('navigates to detail page on row click', async () => {
      const user = userEvent.setup()
      render(<NCRListPage />)

      const rowClickButton = screen.getByText('Mock Row Click')
      await user.click(rowClickButton)

      expect(mockNavigate).toHaveBeenCalledWith('/quality/ncrs/1')
    })
  })

  describe('Error Handling', () => {
    it('shows error message when data fails to load', () => {
      mockUseNCRs.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to fetch'),
        isError: true,
      } as any)

      render(<NCRListPage />)

      expect(screen.getByText(/Failed to load NCRs/i)).toBeInTheDocument()
    })

    it('does not show error message when data loads successfully', () => {
      render(<NCRListPage />)

      expect(screen.queryByText(/Failed to load NCRs/i)).not.toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('shows NCRTable with loading state', () => {
      mockUseNCRs.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        isError: false,
      } as any)

      render(<NCRListPage />)

      // Table should still render, just in loading state
      expect(screen.getByTestId('ncr-table')).toBeInTheDocument()
    })
  })
})
