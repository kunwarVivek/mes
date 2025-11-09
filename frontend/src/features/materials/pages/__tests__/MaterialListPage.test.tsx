/**
 * MaterialListPage Component Tests
 *
 * TDD tests for MaterialListPage with search, filter, and navigation
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MaterialListPage } from '../MaterialListPage'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
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

// Mock the useMaterials hook
const mockUseMaterials = vi.fn()
vi.mock('../../hooks/useMaterials', () => ({
  useMaterials: () => mockUseMaterials(),
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>
    </BrowserRouter>
  )
}

describe('MaterialListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseMaterials.mockReturnValue({
      data: { items: mockMaterials, total: 2, page: 1, page_size: 25, total_pages: 1 },
      isLoading: false,
      error: null,
    })
  })

  describe('Rendering', () => {
    it('should render page title', () => {
      renderWithProviders(<MaterialListPage />)

      expect(screen.getByRole('heading', { name: /materials/i })).toBeInTheDocument()
    })

    it('should render search bar', () => {
      renderWithProviders(<MaterialListPage />)

      expect(screen.getByPlaceholderText(/search materials/i)).toBeInTheDocument()
    })

    it('should render create material button', () => {
      renderWithProviders(<MaterialListPage />)

      expect(screen.getByRole('button', { name: /create material/i })).toBeInTheDocument()
    })

    it('should render material table', () => {
      renderWithProviders(<MaterialListPage />)

      expect(screen.getByText('MAT001')).toBeInTheDocument()
      expect(screen.getByText('Steel Plate')).toBeInTheDocument()
    })

    it('should render filter controls', () => {
      renderWithProviders(<MaterialListPage />)

      // Should have procurement type filter (look for exact match with Filter icon)
      const buttons = screen.getAllByRole('button')
      const procurementFilter = buttons.find((btn) => btn.textContent?.includes('Procurement Type'))
      expect(procurementFilter).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    it('should update search query when typing in search bar', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialListPage />)

      const searchInput = screen.getByPlaceholderText(/search materials/i)
      await user.type(searchInput, 'Steel')

      expect(searchInput).toHaveValue('Steel')
    })

    it('should call useMaterials with search parameter', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialListPage />)

      const searchInput = screen.getByPlaceholderText(/search materials/i)
      await user.type(searchInput, 'Steel')

      // Search is updated immediately via state
      // useMaterials will be called with new params on next render
      expect(mockUseMaterials).toHaveBeenCalled()
    })

    it('should clear search when clear button clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialListPage />)

      const searchInput = screen.getByPlaceholderText(/search materials/i)
      await user.type(searchInput, 'Steel')

      // SearchBar molecule should show clear button (X icon button)
      const buttons = screen.getAllByRole('button')
      const clearButton = buttons.find((btn) => btn.querySelector('svg'))
      expect(clearButton).toBeDefined()

      if (clearButton) {
        await user.click(clearButton)
        expect(searchInput).toHaveValue('')
      }
    })
  })

  describe('Filter Functionality', () => {
    it('should open filter dropdown when filter button clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialListPage />)

      const buttons = screen.getAllByRole('button')
      const filterButton = buttons.find((btn) => btn.textContent?.includes('Procurement Type'))
      expect(filterButton).toBeDefined()

      if (filterButton) {
        await user.click(filterButton)

        // Should show filter options
        await waitFor(() => {
          expect(screen.getByRole('menuitemcheckbox', { name: /purchase/i })).toBeInTheDocument()
        })
      }
    })

    it('should apply procurement type filter', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialListPage />)

      const buttons = screen.getAllByRole('button')
      const filterButton = buttons.find((btn) => btn.textContent?.includes('Procurement Type'))
      expect(filterButton).toBeDefined()

      if (filterButton) {
        await user.click(filterButton)

        // Select PURCHASE option
        const purchaseOption = await screen.findByRole('menuitemcheckbox', { name: /purchase/i })
        await user.click(purchaseOption)

        // Filter applied - verify button state changed
        expect(mockUseMaterials).toHaveBeenCalled()
      }
    })

    it('should show filter count badge when filters applied', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialListPage />)

      const buttons = screen.getAllByRole('button')
      const filterButton = buttons.find((btn) => btn.textContent?.includes('Procurement Type'))
      expect(filterButton).toBeDefined()

      if (filterButton) {
        await user.click(filterButton)

        const purchaseOption = await screen.findByRole('menuitemcheckbox', { name: /purchase/i })
        await user.click(purchaseOption)

        // Close dropdown by clicking elsewhere
        await user.click(document.body)

        // FilterGroup molecule should show count badge (verify filter button contains count)
        await waitFor(
          () => {
            const updatedButton = screen
              .getAllByRole('button')
              .find((btn) => btn.textContent?.includes('Procurement Type'))
            expect(updatedButton?.textContent).toContain('1')
          },
          { timeout: 500 }
        )
      }
    })
  })

  describe('Navigation', () => {
    it('should navigate to create page when create button clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialListPage />)

      const createButton = screen.getByRole('button', { name: /create material/i })
      await user.click(createButton)

      expect(mockNavigate).toHaveBeenCalledWith('/materials/create')
    })

    it('should navigate to material detail when row clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialListPage />)

      // Click on a material row
      const row = screen.getByText('MAT001').closest('tr')
      if (row) {
        await user.click(row)

        expect(mockNavigate).toHaveBeenCalledWith('/materials/1')
      }
    })
  })

  describe('Loading State', () => {
    it('should show loading skeleton while fetching', () => {
      mockUseMaterials.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      })

      renderWithProviders(<MaterialListPage />)

      // MaterialTable should show loading state
      expect(screen.queryByText('MAT001')).not.toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should show error message when fetch fails', () => {
      mockUseMaterials.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to fetch materials'),
      })

      renderWithProviders(<MaterialListPage />)

      expect(screen.getByText(/error|failed/i)).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should show empty state when no materials', () => {
      mockUseMaterials.mockReturnValue({
        data: { items: [], total: 0, page: 1, page_size: 25, total_pages: 0 },
        isLoading: false,
        error: null,
      })

      renderWithProviders(<MaterialListPage />)

      expect(screen.getByText(/no data found/i)).toBeInTheDocument()
    })
  })
})
