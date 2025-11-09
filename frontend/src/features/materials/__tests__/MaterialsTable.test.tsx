/**
 * MaterialsTable Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MaterialsTable } from '../components/MaterialsTable'
import type { Material } from '../types/material.types'

const mockMaterials: Material[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    material_number: 'MAT001',
    material_name: 'Test Material 1',
    material_category_id: 1,
    base_uom_id: 1,
    procurement_type: 'PURCHASE',
    mrp_type: 'MRP',
    safety_stock: 100,
    reorder_point: 50,
    lot_size: 10,
    lead_time_days: 5,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    material_number: 'MAT002',
    material_name: 'Test Material 2',
    material_category_id: 2,
    base_uom_id: 2,
    procurement_type: 'MANUFACTURE',
    mrp_type: 'REORDER',
    safety_stock: 200,
    reorder_point: 100,
    lot_size: 20,
    lead_time_days: 10,
    is_active: false,
    created_at: '2024-01-02T00:00:00Z',
  },
]

describe('MaterialsTable', () => {
  it('should render loading skeleton when loading', () => {
    render(<MaterialsTable materials={[]} isLoading={true} />)

    // Should show skeleton, not empty state
    expect(screen.queryByText('No materials found')).not.toBeInTheDocument()
  })

  it('should render empty state when no materials', () => {
    render(<MaterialsTable materials={[]} isLoading={false} />)

    expect(screen.getByText('No materials found')).toBeInTheDocument()
  })

  it('should render materials table with data', () => {
    render(<MaterialsTable materials={mockMaterials} />)

    expect(screen.getByText('MAT001')).toBeInTheDocument()
    expect(screen.getByText('Test Material 1')).toBeInTheDocument()
    expect(screen.getByText('MAT002')).toBeInTheDocument()
    expect(screen.getByText('Test Material 2')).toBeInTheDocument()
  })

  it('should call onEdit when edit button clicked', async () => {
    const onEdit = vi.fn()
    const user = userEvent.setup()

    render(<MaterialsTable materials={mockMaterials} onEdit={onEdit} />)

    const editButtons = screen.getAllByText('Edit')
    await user.click(editButtons[0])

    expect(onEdit).toHaveBeenCalledWith(mockMaterials[0])
  })

  it('should call onDelete when delete button clicked', async () => {
    const onDelete = vi.fn()
    const user = userEvent.setup()

    render(<MaterialsTable materials={mockMaterials} onDelete={onDelete} />)

    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    expect(onDelete).toHaveBeenCalledWith(mockMaterials[0])
  })

  it('should call onRowClick when row clicked', async () => {
    const onRowClick = vi.fn()
    const user = userEvent.setup()

    render(<MaterialsTable materials={mockMaterials} onRowClick={onRowClick} />)

    const row = screen.getByText('Test Material 1').closest('tr')
    await user.click(row!)

    expect(onRowClick).toHaveBeenCalledWith(mockMaterials[0])
  })

  it('should display status badges correctly', () => {
    render(<MaterialsTable materials={mockMaterials} />)

    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })

  it('should display procurement and MRP type badges', () => {
    render(<MaterialsTable materials={mockMaterials} />)

    expect(screen.getByText('PURCHASE')).toBeInTheDocument()
    expect(screen.getByText('MANUFACTURE')).toBeInTheDocument()
    expect(screen.getByText('MRP')).toBeInTheDocument()
    expect(screen.getByText('REORDER')).toBeInTheDocument()
  })
})
