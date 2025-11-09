/**
 * BOMTreeView Component Tests
 *
 * TDD: RED phase - These tests will fail initially
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BOMTreeView } from '../components/BOMTreeView'
import type { BOMLineWithChildren } from '../types/bom.types'

const mockFlatLine: BOMLineWithChildren = {
  id: 1,
  bom_header_id: 1,
  line_number: 10,
  component_material_id: 101,
  component_material_name: 'Frame Assembly',
  quantity: 1,
  unit_of_measure_id: 1,
  unit_of_measure: 'EA',
  scrap_factor: 0,
  is_phantom: false,
  backflush: false,
  created_at: '2024-01-01T00:00:00Z'
}

const mockHierarchicalLines: BOMLineWithChildren[] = [
  {
    id: 1,
    bom_header_id: 1,
    line_number: 10,
    component_material_id: 101,
    component_material_name: 'Frame Assembly',
    quantity: 1,
    unit_of_measure_id: 1,
    unit_of_measure: 'EA',
    scrap_factor: 5,
    is_phantom: false,
    backflush: false,
    created_at: '2024-01-01T00:00:00Z',
    children: [
      {
        id: 2,
        bom_header_id: 1,
        line_number: 20,
        component_material_id: 102,
        component_material_name: 'Steel Tube',
        quantity: 2,
        unit_of_measure_id: 1,
        unit_of_measure: 'EA',
        scrap_factor: 0,
        is_phantom: false,
        backflush: true,
        created_at: '2024-01-01T00:00:00Z'
      }
    ]
  },
  {
    id: 3,
    bom_header_id: 1,
    line_number: 30,
    component_material_id: 103,
    component_material_name: 'Wheel Assembly',
    quantity: 2,
    unit_of_measure_id: 1,
    unit_of_measure: 'EA',
    scrap_factor: 0,
    is_phantom: true,
    backflush: false,
    created_at: '2024-01-01T00:00:00Z',
    children: []
  }
]

describe('BOMTreeView', () => {
  it('renders BOM line with material name and quantity', () => {
    render(<BOMTreeView lines={[mockFlatLine]} />)

    expect(screen.getByText('Frame Assembly')).toBeInTheDocument()
    expect(screen.getByText(/Qty: 1 EA/)).toBeInTheDocument()
  })

  it('displays line number (sequence)', () => {
    render(<BOMTreeView lines={[mockFlatLine]} />)

    expect(screen.getByText(/Line: 10/)).toBeInTheDocument()
  })

  it('shows scrap factor when greater than zero', () => {
    const lineWithScrap = {
      ...mockFlatLine,
      scrap_factor: 5
    }

    render(<BOMTreeView lines={[lineWithScrap]} />)

    expect(screen.getByText(/Scrap: 5%/)).toBeInTheDocument()
  })

  it('displays phantom badge for phantom BOMs', () => {
    const phantomLine = {
      ...mockFlatLine,
      is_phantom: true
    }

    render(<BOMTreeView lines={[phantomLine]} />)

    expect(screen.getByText('PHANTOM')).toBeInTheDocument()
  })

  it('shows expand button for lines with children', () => {
    render(<BOMTreeView lines={mockHierarchicalLines} />)

    // Should have expand arrow for first line with children
    const expandButtons = screen.getAllByRole('button', { name: /expand/i })
    expect(expandButtons.length).toBeGreaterThan(0)
  })

  it('does not show expand button for lines without children', () => {
    render(<BOMTreeView lines={[mockFlatLine]} />)

    // Should not have expand button
    expect(screen.queryByRole('button', { name: /expand/i })).not.toBeInTheDocument()
  })

  it('expands and shows children when expand button clicked', async () => {
    const user = userEvent.setup()

    render(<BOMTreeView lines={mockHierarchicalLines} />)

    // Initially children should not be visible
    expect(screen.queryByText('Steel Tube')).not.toBeInTheDocument()

    // Click expand
    const expandButton = screen.getAllByRole('button', { name: /expand/i })[0]
    await user.click(expandButton)

    // Children should now be visible
    expect(screen.getByText('Steel Tube')).toBeInTheDocument()
  })

  it('collapses children when collapse button clicked', async () => {
    const user = userEvent.setup()

    render(<BOMTreeView lines={mockHierarchicalLines} />)

    // Expand first
    const expandButton = screen.getAllByRole('button', { name: /expand/i })[0]
    await user.click(expandButton)
    expect(screen.getByText('Steel Tube')).toBeInTheDocument()

    // Then collapse
    const collapseButton = screen.getAllByRole('button', { name: /collapse/i })[0]
    await user.click(collapseButton)

    // Children should be hidden again
    expect(screen.queryByText('Steel Tube')).not.toBeInTheDocument()
  })

  it('applies correct indentation for nested levels', () => {
    render(<BOMTreeView lines={mockHierarchicalLines} />)

    const parentLine = screen.getByText('Frame Assembly').closest('.bom-tree-node')
    expect(parentLine).toHaveStyle({ paddingLeft: '8px' })
  })

  it('calls onEdit when edit button clicked', async () => {
    const onEdit = vi.fn()
    const user = userEvent.setup()

    render(<BOMTreeView lines={[mockFlatLine]} onEdit={onEdit} />)

    const editButton = screen.getByRole('button', { name: /edit/i })
    await user.click(editButton)

    expect(onEdit).toHaveBeenCalledWith(mockFlatLine)
  })

  it('calls onDelete when delete button clicked', async () => {
    const onDelete = vi.fn()
    const user = userEvent.setup()

    render(<BOMTreeView lines={[mockFlatLine]} onDelete={onDelete} />)

    const deleteButton = screen.getByRole('button', { name: /delete/i })
    await user.click(deleteButton)

    expect(onDelete).toHaveBeenCalledWith(mockFlatLine.id)
  })

  it('calls onAddChild when add child button clicked', async () => {
    const onAddChild = vi.fn()
    const user = userEvent.setup()

    render(<BOMTreeView lines={[mockFlatLine]} onAddChild={onAddChild} />)

    const addChildButton = screen.getByRole('button', { name: /add child/i })
    await user.click(addChildButton)

    expect(onAddChild).toHaveBeenCalledWith(mockFlatLine)
  })

  it('renders multi-level hierarchy correctly', async () => {
    const user = userEvent.setup()

    const multiLevel: BOMLineWithChildren[] = [
      {
        id: 1,
        bom_header_id: 1,
        line_number: 10,
        component_material_id: 101,
        component_material_name: 'Level 1',
        quantity: 1,
        unit_of_measure_id: 1,
        unit_of_measure: 'EA',
        scrap_factor: 0,
        is_phantom: false,
        backflush: false,
        created_at: '2024-01-01T00:00:00Z',
        children: [
          {
            id: 2,
            bom_header_id: 1,
            line_number: 20,
            component_material_id: 102,
            component_material_name: 'Level 2',
            quantity: 2,
            unit_of_measure_id: 1,
            unit_of_measure: 'EA',
            scrap_factor: 0,
            is_phantom: false,
            backflush: false,
            created_at: '2024-01-01T00:00:00Z',
            children: [
              {
                id: 3,
                bom_header_id: 1,
                line_number: 30,
                component_material_id: 103,
                component_material_name: 'Level 3',
                quantity: 3,
                unit_of_measure_id: 1,
                unit_of_measure: 'EA',
                scrap_factor: 0,
                is_phantom: false,
                backflush: false,
                created_at: '2024-01-01T00:00:00Z'
              }
            ]
          }
        ]
      }
    ]

    const { container } = render(<BOMTreeView lines={multiLevel} />)

    // Expand level 1
    const level1Button = screen.getByText('Level 1').closest('.bom-tree-node')?.querySelector('button')
    expect(level1Button).toBeInTheDocument()
    await user.click(level1Button!)

    // Level 2 should now be visible
    expect(screen.getByText('Level 2')).toBeInTheDocument()

    // Expand level 2
    const level2Button = screen.getByText('Level 2').closest('.bom-tree-node')?.querySelector('button')
    expect(level2Button).toBeInTheDocument()
    await user.click(level2Button!)

    // Level 3 should now be visible
    expect(screen.getByText('Level 3')).toBeInTheDocument()
  })

  it('renders empty state when no lines provided', () => {
    render(<BOMTreeView lines={[]} />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
