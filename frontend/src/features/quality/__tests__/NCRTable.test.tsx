/**
 * NCRTable Component Tests
 *
 * TDD: Testing NCR table display with badges and actions
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NCRTable } from '../components/NCRTable'
import type { NCR } from '../types/ncr.types'

const mockNCRs: NCR[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2025-001',
    status: 'OPEN',
    defect_type: 'MATERIAL',
    work_order_id: 100,
    material_id: 50,
    quantity_affected: 25,
    description: 'Material defect in batch XYZ',
    root_cause: null,
    corrective_action: null,
    preventive_action: null,
    reported_by: 1,
    assigned_to: null,
    reported_at: '2025-01-01T10:00:00Z',
    closed_at: null,
    created_at: '2025-01-01T10:00:00Z',
    updated_at: null,
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    ncr_number: 'NCR-2025-002',
    status: 'INVESTIGATING',
    defect_type: 'PROCESS',
    work_order_id: 101,
    material_id: 51,
    quantity_affected: 10,
    description: 'Process deviation observed',
    root_cause: 'Improper temperature control',
    corrective_action: null,
    preventive_action: null,
    reported_by: 2,
    assigned_to: 3,
    reported_at: '2025-01-02T14:30:00Z',
    closed_at: null,
    created_at: '2025-01-02T14:30:00Z',
    updated_at: '2025-01-02T16:00:00Z',
  },
]

describe('NCRTable', () => {
  it('should render table with NCRs', () => {
    render(<NCRTable ncrs={mockNCRs} onView={vi.fn()} onDelete={vi.fn()} />)

    expect(screen.getByText('NCR-2025-001')).toBeInTheDocument()
    expect(screen.getByText('NCR-2025-002')).toBeInTheDocument()
    expect(screen.getByText('MATERIAL')).toBeInTheDocument()
    expect(screen.getByText('PROCESS')).toBeInTheDocument()
  })

  it('should display status badges with correct variants', () => {
    render(<NCRTable ncrs={mockNCRs} onView={vi.fn()} onDelete={vi.fn()} />)

    const openBadges = screen.getAllByText('OPEN')
    const investigatingBadges = screen.getAllByText('INVESTIGATING')

    expect(openBadges[0]).toHaveClass('badge--error')
    expect(investigatingBadges[0]).toHaveClass('badge--warning')
  })

  it('should display defect type badges', () => {
    render(<NCRTable ncrs={mockNCRs} onView={vi.fn()} onDelete={vi.fn()} />)

    const materialBadge = screen.getByText('MATERIAL')
    const processBadge = screen.getByText('PROCESS')

    expect(materialBadge).toHaveClass('badge--error')
    expect(processBadge).toHaveClass('badge--warning')
  })

  it('should display quantity affected', () => {
    render(<NCRTable ncrs={mockNCRs} onView={vi.fn()} onDelete={vi.fn()} />)

    expect(screen.getByText('25')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('should truncate long descriptions', () => {
    render(<NCRTable ncrs={mockNCRs} onView={vi.fn()} onDelete={vi.fn()} />)

    const description = screen.getByText('Material defect in batch XYZ')
    expect(description).toHaveClass('max-w-md')
    expect(description).toHaveClass('truncate')
  })

  it('should format dates correctly', () => {
    render(<NCRTable ncrs={mockNCRs} onView={vi.fn()} onDelete={vi.fn()} />)

    // Dates should be formatted to locale string
    expect(screen.getByText('1/1/2025')).toBeInTheDocument()
    expect(screen.getByText('2/1/2025')).toBeInTheDocument() // 2025-01-02 -> 2/1/2025 in DD/MM/YYYY locales
  })

  it('should call onView when View button clicked', async () => {
    const onView = vi.fn()
    const user = userEvent.setup()

    render(<NCRTable ncrs={mockNCRs} onView={onView} onDelete={vi.fn()} />)

    const viewButtons = screen.getAllByRole('button', { name: /View/i })
    await user.click(viewButtons[0])

    expect(onView).toHaveBeenCalledWith(mockNCRs[0])
  })

  it('should call onDelete when Delete button clicked', async () => {
    const onDelete = vi.fn()
    const user = userEvent.setup()

    render(<NCRTable ncrs={mockNCRs} onView={vi.fn()} onDelete={onDelete} />)

    const deleteButtons = screen.getAllByRole('button', { name: /Delete/i })
    await user.click(deleteButtons[0])

    expect(onDelete).toHaveBeenCalledWith(1)
  })

  it('should render loading state', () => {
    render(<NCRTable ncrs={[]} onView={vi.fn()} onDelete={vi.fn()} isLoading={true} />)

    expect(screen.getByText(/Loading NCRs/i)).toBeInTheDocument()
  })

  it('should render empty state when no NCRs', () => {
    render(<NCRTable ncrs={[]} onView={vi.fn()} onDelete={vi.fn()} />)

    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })
})
