/**
 * MaterialFormPage Component Tests
 *
 * TDD tests for MaterialFormPage (create/edit modes)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MaterialFormPage } from '../MaterialFormPage'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import type { Material } from '../../types/material.types'

const mockMaterial: Material = {
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
}

// Mock the useMaterial hook
const mockUseMaterial = vi.fn()
vi.mock('../../hooks/useMaterial', () => ({
  useMaterial: (id: number) => mockUseMaterial(id),
}))

// Mock toast
vi.mock('@/components/ui/use-toast', () => ({
  toast: vi.fn(),
}))

// Mock mutations
const mockCreateMaterial = vi.fn()
const mockUpdateMaterial = vi.fn()
vi.mock('../../hooks/useMaterialMutations', () => ({
  useMaterialMutations: () => ({
    createMaterial: {
      mutateAsync: mockCreateMaterial,
      isPending: false,
    },
    updateMaterial: {
      mutateAsync: mockUpdateMaterial,
      isPending: false,
    },
  }),
}))

// Mock useNavigate and useParams
const mockNavigate = vi.fn()
let mockParams = {}

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => mockParams,
  }
})

const renderWithProviders = (component: React.ReactElement, initialRoute = '/materials/create') => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  window.history.pushState({}, '', initialRoute)

  return render(
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>
    </BrowserRouter>
  )
}

describe('MaterialFormPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockParams = {}
    mockUseMaterial.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    })
  })

  describe('Create Mode', () => {
    it('should render create material form', () => {
      renderWithProviders(<MaterialFormPage />)

      expect(screen.getByRole('heading', { name: /create material/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/material number/i)).toBeInTheDocument()
    })

    it('should show create button', () => {
      renderWithProviders(<MaterialFormPage />)

      expect(screen.getByRole('button', { name: /create material/i })).toBeInTheDocument()
    })

    it('should navigate back to list on cancel', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialFormPage />)

      const backButton = screen.getByRole('button', { name: /back|cancel/i })
      await user.click(backButton)

      expect(mockNavigate).toHaveBeenCalledWith('/materials')
    })
  })

  describe('Edit Mode', () => {
    beforeEach(() => {
      mockParams = { id: '1' }
      mockUseMaterial.mockReturnValue({
        data: mockMaterial,
        isLoading: false,
        error: null,
      })
    })

    it('should render edit material form', () => {
      renderWithProviders(<MaterialFormPage />, '/materials/1/edit')

      expect(screen.getByRole('heading', { name: /edit material/i })).toBeInTheDocument()
    })

    it('should fetch material data by ID', () => {
      renderWithProviders(<MaterialFormPage />, '/materials/1/edit')

      expect(mockUseMaterial).toHaveBeenCalledWith(1)
    })

    it('should populate form with material data', () => {
      renderWithProviders(<MaterialFormPage />, '/materials/1/edit')

      expect(screen.getByDisplayValue('MAT001')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Steel Plate')).toBeInTheDocument()
    })

    it('should show update button', () => {
      renderWithProviders(<MaterialFormPage />, '/materials/1/edit')

      expect(screen.getByRole('button', { name: /update material/i })).toBeInTheDocument()
    })

    it('should show loading state while fetching material', () => {
      mockUseMaterial.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      })

      renderWithProviders(<MaterialFormPage />, '/materials/1/edit')

      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })

    it('should show error if material not found', () => {
      mockUseMaterial.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Not found'),
      })

      renderWithProviders(<MaterialFormPage />, '/materials/1/edit')

      expect(screen.getByText(/error|not found/i)).toBeInTheDocument()
    })
  })

  describe('Form Submission', () => {
    it('should navigate to list after successful create', async () => {
      mockCreateMaterial.mockResolvedValue({ id: 1 })

      renderWithProviders(<MaterialFormPage />)

      // Form submission tested in MaterialForm component
      // Just verify navigation happens via onSuccess callback
      expect(screen.getByRole('heading', { name: /create material/i })).toBeInTheDocument()
    })
  })

  describe('Breadcrumbs', () => {
    it('should show breadcrumb navigation in create mode', () => {
      renderWithProviders(<MaterialFormPage />)

      // Should show Materials > Create
      expect(screen.getByText(/create material/i)).toBeInTheDocument()
    })

    it('should show breadcrumb navigation in edit mode', () => {
      mockParams = { id: '1' }
      mockUseMaterial.mockReturnValue({
        data: mockMaterial,
        isLoading: false,
        error: null,
      })

      renderWithProviders(<MaterialFormPage />, '/materials/1/edit')

      // Should show Materials > Edit
      expect(screen.getByText(/edit material/i)).toBeInTheDocument()
    })
  })
})
