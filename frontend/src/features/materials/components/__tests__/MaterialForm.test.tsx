/**
 * MaterialForm Component Tests
 *
 * TDD tests for MaterialForm using React Hook Form + shadcn
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MaterialForm } from '../MaterialForm'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { Material } from '../../types/material.types'

// Mock the toast hook
vi.mock('@/components/ui/use-toast', () => ({
  toast: vi.fn(),
}))

// Mock mutations hook
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

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>)
}

describe('MaterialForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Create Mode', () => {
    it('should render all form fields in create mode', () => {
      renderWithProviders(<MaterialForm />)

      expect(screen.getByLabelText(/material number/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/material name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/material category/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/base uom/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/procurement type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/mrp type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/safety stock/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/reorder point/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/lot size/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/lead time/i)).toBeInTheDocument()
    })

    it('should show validation errors for required fields', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialForm />)

      const submitButton = screen.getByRole('button', { name: /create material/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/material number is required/i)).toBeInTheDocument()
        expect(screen.getByText(/material name is required/i)).toBeInTheDocument()
      })
    })

    it('should validate material number format', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialForm />)

      const materialNumberInput = screen.getByLabelText(/material number/i)
      await user.type(materialNumberInput, 'mat-123')

      const submitButton = screen.getByRole('button', { name: /create material/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(
          screen.getByText(/material number must be uppercase alphanumeric only/i)
        ).toBeInTheDocument()
      })
    })

    it('should validate material number length (max 10)', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialForm />)

      const materialNumberInput = screen.getByLabelText(/material number/i)
      await user.type(materialNumberInput, 'MATERIAL12345')

      const submitButton = screen.getByRole('button', { name: /create material/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(
          screen.getByText(/material number must be at most 10 characters/i)
        ).toBeInTheDocument()
      })
    })

    it('should validate material name length (max 200)', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialForm />)

      const materialNameInput = screen.getByLabelText(/material name/i)
      await user.type(materialNameInput, 'A'.repeat(201))

      const submitButton = screen.getByRole('button', { name: /create material/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(
          screen.getByText(/material name must be at most 200 characters/i)
        ).toBeInTheDocument()
      })
    })

    it('should submit valid form data', async () => {
      const user = userEvent.setup()
      const onSuccess = vi.fn()
      mockCreateMaterial.mockResolvedValue({ id: 1 })

      renderWithProviders(<MaterialForm onSuccess={onSuccess} />)

      await user.type(screen.getByLabelText(/material number/i), 'MAT001')
      await user.type(screen.getByLabelText(/material name/i), 'Test Material')
      await user.type(screen.getByLabelText(/description/i), 'Test description')

      // Select category and UOM (assuming select components)
      await user.type(screen.getByLabelText(/material category/i), '1')
      await user.type(screen.getByLabelText(/base uom/i), '1')

      await user.click(screen.getByRole('button', { name: /create material/i }))

      await waitFor(() => {
        expect(mockCreateMaterial).toHaveBeenCalledWith(
          expect.objectContaining({
            material_number: 'MAT001',
            material_name: 'Test Material',
            description: 'Test description',
            material_category_id: 1,
            base_uom_id: 1,
          })
        )
        expect(onSuccess).toHaveBeenCalled()
      })
    })

    it('should clear validation errors when user corrects input', async () => {
      const user = userEvent.setup()
      renderWithProviders(<MaterialForm />)

      const submitButton = screen.getByRole('button', { name: /create material/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/material number is required/i)).toBeInTheDocument()
      })

      const materialNumberInput = screen.getByLabelText(/material number/i)
      await user.type(materialNumberInput, 'MAT001')

      await waitFor(() => {
        expect(screen.queryByText(/material number is required/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Edit Mode', () => {
    const existingMaterial: Material = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      material_number: 'MAT001',
      material_name: 'Existing Material',
      description: 'Existing description',
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

    it('should populate form with existing material data', () => {
      renderWithProviders(<MaterialForm materialId={1} defaultValues={existingMaterial} />)

      expect(screen.getByDisplayValue('MAT001')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Existing Material')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Existing description')).toBeInTheDocument()
    })

    it('should disable material number field in edit mode', () => {
      renderWithProviders(<MaterialForm materialId={1} defaultValues={existingMaterial} />)

      const materialNumberInput = screen.getByLabelText(/material number/i)
      expect(materialNumberInput).toBeDisabled()
    })

    it('should submit only changed fields', async () => {
      const user = userEvent.setup()
      mockUpdateMaterial.mockResolvedValue({ id: 1 })

      renderWithProviders(<MaterialForm materialId={1} defaultValues={existingMaterial} />)

      const materialNameInput = screen.getByLabelText(/material name/i)
      await user.clear(materialNameInput)
      await user.type(materialNameInput, 'Updated Material')

      await user.click(screen.getByRole('button', { name: /update material/i }))

      await waitFor(() => {
        expect(mockUpdateMaterial).toHaveBeenCalledWith({
          id: 1,
          data: {
            material_name: 'Updated Material',
          },
        })
      })
    })
  })

  describe('Loading States', () => {
    it('should disable form during submission', async () => {
      const user = userEvent.setup()
      mockCreateMaterial.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      renderWithProviders(<MaterialForm />)

      await user.type(screen.getByLabelText(/material number/i), 'MAT001')
      await user.type(screen.getByLabelText(/material name/i), 'Test')
      await user.type(screen.getByLabelText(/material category/i), '1')
      await user.type(screen.getByLabelText(/base uom/i), '1')

      const submitButton = screen.getByRole('button', { name: /create material/i })
      await user.click(submitButton)

      expect(submitButton).toBeDisabled()
    })
  })

  describe('Default Values', () => {
    it('should use default organization and plant IDs', () => {
      const defaultValues = {
        organization_id: 5,
        plant_id: 10,
      }

      renderWithProviders(<MaterialForm defaultValues={defaultValues} />)

      // These would be hidden fields or set in the form context
      // Just verify the form renders without errors
      expect(screen.getByLabelText(/material number/i)).toBeInTheDocument()
    })

    it('should set default values for numeric fields', () => {
      renderWithProviders(<MaterialForm />)

      expect(screen.getByLabelText(/safety stock/i)).toHaveValue(0)
      expect(screen.getByLabelText(/reorder point/i)).toHaveValue(0)
      expect(screen.getByLabelText(/lot size/i)).toHaveValue(1)
      expect(screen.getByLabelText(/lead time/i)).toHaveValue(0)
    })
  })
})
