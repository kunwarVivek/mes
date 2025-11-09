/**
 * BOMsTable Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BOMsTable } from '../components/BOMsTable'
import type { BOM } from '../types/bom.types'

const mockBOMs: BOM[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    bom_number: 'BOM001',
    material_id: 1,
    bom_version: 1,
    bom_name: 'Test BOM 1',
    bom_type: 'PRODUCTION',
    base_quantity: 1,
    unit_of_measure_id: 1,
    is_active: true,
    created_by_user_id: 1,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    bom_number: 'BOM002',
    material_id: 2,
    bom_version: 2,
    bom_name: 'Test BOM 2',
    bom_type: 'ENGINEERING',
    base_quantity: 2,
    unit_of_measure_id: 2,
    is_active: false,
    created_by_user_id: 1,
    created_at: '2024-01-02T00:00:00Z',
  },
]

describe('BOMsTable', () => {
  it('should render loading skeleton when loading', () => {
    render(<BOMsTable boms={[]} isLoading={true} />)

    // Should show skeleton, not empty state
    expect(screen.queryByText('No BOMs found')).not.toBeInTheDocument()
  })

  it('should render empty state when no BOMs', () => {
    render(<BOMsTable boms={[]} isLoading={false} />)

    expect(screen.getByText('No BOMs found')).toBeInTheDocument()
  })

  it('should render BOMs table with data', () => {
    render(<BOMsTable boms={mockBOMs} />)

    expect(screen.getByText('BOM001')).toBeInTheDocument()
    expect(screen.getByText('Test BOM 1')).toBeInTheDocument()
    expect(screen.getByText('BOM002')).toBeInTheDocument()
    expect(screen.getByText('Test BOM 2')).toBeInTheDocument()
  })

  it('should call onEdit when edit button clicked', async () => {
    const onEdit = vi.fn()
    const user = userEvent.setup()

    render(<BOMsTable boms={mockBOMs} onEdit={onEdit} />)

    const editButtons = screen.getAllByText('Edit')
    await user.click(editButtons[0])

    expect(onEdit).toHaveBeenCalledWith(mockBOMs[0])
  })

  it('should call onDelete when delete button clicked', async () => {
    const onDelete = vi.fn()
    const user = userEvent.setup()

    render(<BOMsTable boms={mockBOMs} onDelete={onDelete} />)

    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    expect(onDelete).toHaveBeenCalledWith(mockBOMs[0])
  })

  it('should call onRowClick when row clicked', async () => {
    const onRowClick = vi.fn()
    const user = userEvent.setup()

    render(<BOMsTable boms={mockBOMs} onRowClick={onRowClick} />)

    const row = screen.getByText('Test BOM 1').closest('tr')
    await user.click(row!)

    expect(onRowClick).toHaveBeenCalledWith(mockBOMs[0])
  })

  it('should display status badges correctly', () => {
    render(<BOMsTable boms={mockBOMs} />)

    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })

  it('should display BOM type badges', () => {
    render(<BOMsTable boms={mockBOMs} />)

    expect(screen.getByText('PRODUCTION')).toBeInTheDocument()
    expect(screen.getByText('ENGINEERING')).toBeInTheDocument()
  })
})
