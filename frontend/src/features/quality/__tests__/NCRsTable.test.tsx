/**
 * NCRsTable Component Tests
 *
 * TDD: Testing table rendering and interactions
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NCRsTable } from '../components/NCRsTable'
import type { NCR } from '../types/quality.types'

const mockNCRs: NCR[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2024-001',
    work_order_id: 100,
    material_id: 50,
    defect_type: 'DIMENSIONAL',
    defect_description: 'Part dimension out of tolerance by 0.5mm',
    quantity_defective: 5,
    status: 'OPEN',
    reported_by_user_id: 1,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2024-002',
    work_order_id: 101,
    material_id: 51,
    defect_type: 'VISUAL',
    defect_description: 'Surface scratches visible on part',
    quantity_defective: 3,
    status: 'IN_REVIEW',
    reported_by_user_id: 2,
    created_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 3,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2024-003',
    work_order_id: 102,
    material_id: 52,
    defect_type: 'FUNCTIONAL',
    defect_description: 'Component fails functional test',
    quantity_defective: 10,
    status: 'RESOLVED',
    reported_by_user_id: 1,
    resolution_notes: 'Parts reworked',
    resolved_by_user_id: 3,
    resolved_at: '2024-01-03T00:00:00Z',
    created_at: '2024-01-03T00:00:00Z',
  },
]

describe('NCRsTable', () => {
  it('should render loading skeletons when isLoading is true', () => {
    render(<NCRsTable ncrs={[]} isLoading={true} />)
    const skeletons = document.querySelectorAll('.ncrs-table-skeleton > *')
    expect(skeletons.length).toBe(5)
  })

  it('should render empty state when no NCRs', () => {
    render(<NCRsTable ncrs={[]} />)
    expect(screen.getByText('No NCRs found')).toBeInTheDocument()
    expect(
      screen.getByText(/No non-conformance reports match your filters/i)
    ).toBeInTheDocument()
  })

  it('should render table with NCRs', () => {
    render(<NCRsTable ncrs={mockNCRs} />)

    expect(screen.getByText('NCR-2024-001')).toBeInTheDocument()
    expect(screen.getByText('NCR-2024-002')).toBeInTheDocument()
    expect(screen.getByText('NCR-2024-003')).toBeInTheDocument()
  })

  it('should display correct status badges', () => {
    render(<NCRsTable ncrs={mockNCRs} />)

    expect(screen.getByText('OPEN')).toBeInTheDocument()
    expect(screen.getByText('IN_REVIEW')).toBeInTheDocument()
    expect(screen.getByText('RESOLVED')).toBeInTheDocument()
  })

  it('should display correct defect type badges', () => {
    render(<NCRsTable ncrs={mockNCRs} />)

    expect(screen.getByText('DIMENSIONAL')).toBeInTheDocument()
    expect(screen.getByText('VISUAL')).toBeInTheDocument()
    expect(screen.getByText('FUNCTIONAL')).toBeInTheDocument()
  })

  it('should truncate long descriptions', () => {
    const longDescriptionNCR: NCR = {
      ...mockNCRs[0],
      defect_description:
        'This is a very long description that exceeds 50 characters and should be truncated',
    }

    render(<NCRsTable ncrs={[longDescriptionNCR]} />)

    const description = screen.getByText(/This is a very long description/i)
    expect(description.textContent).toContain('...')
  })

  it('should show Review button for OPEN NCRs', () => {
    const onReview = vi.fn()
    render(<NCRsTable ncrs={[mockNCRs[0]]} onReview={onReview} />)

    expect(screen.getByText('Review')).toBeInTheDocument()
  })

  it('should show Resolve button for IN_REVIEW NCRs', () => {
    const onResolve = vi.fn()
    render(<NCRsTable ncrs={[mockNCRs[1]]} onResolve={onResolve} />)

    expect(screen.getByText('Resolve')).toBeInTheDocument()
  })

  it('should not show Review/Resolve buttons for RESOLVED NCRs', () => {
    const onReview = vi.fn()
    const onResolve = vi.fn()
    render(<NCRsTable ncrs={[mockNCRs[2]]} onReview={onReview} onResolve={onResolve} />)

    expect(screen.queryByText('Review')).not.toBeInTheDocument()
    expect(screen.queryByText('Resolve')).not.toBeInTheDocument()
  })

  it('should call onReview when Review button is clicked', async () => {
    const user = userEvent.setup()
    const onReview = vi.fn()
    render(<NCRsTable ncrs={[mockNCRs[0]]} onReview={onReview} />)

    const reviewButton = screen.getByText('Review')
    await user.click(reviewButton)

    expect(onReview).toHaveBeenCalledWith(mockNCRs[0])
  })

  it('should call onResolve when Resolve button is clicked', async () => {
    const user = userEvent.setup()
    const onResolve = vi.fn()
    render(<NCRsTable ncrs={[mockNCRs[1]]} onResolve={onResolve} />)

    const resolveButton = screen.getByText('Resolve')
    await user.click(resolveButton)

    expect(onResolve).toHaveBeenCalledWith(mockNCRs[1])
  })

  it('should call onDelete when Delete button is clicked', async () => {
    const user = userEvent.setup()
    const onDelete = vi.fn()
    render(<NCRsTable ncrs={mockNCRs} onDelete={onDelete} />)

    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    expect(onDelete).toHaveBeenCalledWith(mockNCRs[0])
  })

  it('should call onRowClick when row is clicked', async () => {
    const user = userEvent.setup()
    const onRowClick = vi.fn()
    render(<NCRsTable ncrs={mockNCRs} onRowClick={onRowClick} />)

    const row = screen.getByText('NCR-2024-001').closest('tr')
    if (row) {
      await user.click(row)
    }

    expect(onRowClick).toHaveBeenCalledWith(mockNCRs[0])
  })

  it('should not propagate click when action button is clicked', async () => {
    const user = userEvent.setup()
    const onRowClick = vi.fn()
    const onDelete = vi.fn()
    render(<NCRsTable ncrs={mockNCRs} onRowClick={onRowClick} onDelete={onDelete} />)

    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    expect(onDelete).toHaveBeenCalledWith(mockNCRs[0])
    expect(onRowClick).not.toHaveBeenCalled()
  })
})
