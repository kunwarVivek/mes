/**
 * ProductionPlansTable Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProductionPlansTable } from '../components/ProductionPlansTable'
import type { ProductionPlan } from '../types/production.types'

const mockPlans: ProductionPlan[] = [
  {
    id: 1,
    organization_id: 1,
    plan_code: 'PLAN001',
    plan_name: 'Q1 Production Plan',
    start_date: '2024-01-01',
    end_date: '2024-03-31',
    status: 'DRAFT',
    created_by_user_id: 1,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    organization_id: 1,
    plan_code: 'PLAN002',
    plan_name: 'Q2 Production Plan',
    start_date: '2024-04-01',
    end_date: '2024-06-30',
    status: 'APPROVED',
    created_by_user_id: 1,
    created_at: '2024-01-02T00:00:00Z',
  },
]

describe('ProductionPlansTable', () => {
  it('should render empty state when no plans', () => {
    render(<ProductionPlansTable plans={[]} />)
    expect(screen.getByText(/No production plans found/i)).toBeInTheDocument()
  })

  it('should render plans list', () => {
    render(<ProductionPlansTable plans={mockPlans} />)

    expect(screen.getByText('PLAN001')).toBeInTheDocument()
    expect(screen.getByText('Q1 Production Plan')).toBeInTheDocument()
    expect(screen.getByText('PLAN002')).toBeInTheDocument()
    expect(screen.getByText('Q2 Production Plan')).toBeInTheDocument()
  })

  it('should render status badges with correct colors', () => {
    render(<ProductionPlansTable plans={mockPlans} />)

    const draftBadge = screen.getByText('DRAFT')
    const approvedBadge = screen.getByText('APPROVED')

    expect(draftBadge).toHaveClass('status-draft')
    expect(approvedBadge).toHaveClass('status-approved')
  })

  it('should display formatted dates', () => {
    render(<ProductionPlansTable plans={mockPlans} />)

    expect(screen.getByText(/2024-01-01/)).toBeInTheDocument()
    expect(screen.getByText(/2024-03-31/)).toBeInTheDocument()
  })

  it('should call onEdit when edit button clicked', async () => {
    const onEdit = vi.fn()
    const user = userEvent.setup()

    render(<ProductionPlansTable plans={mockPlans} onEdit={onEdit} />)

    const editButtons = screen.getAllByRole('button', { name: /edit/i })
    await user.click(editButtons[0])

    expect(onEdit).toHaveBeenCalledWith(mockPlans[0])
  })

  it('should call onDelete when delete button clicked', async () => {
    const onDelete = vi.fn()
    const user = userEvent.setup()

    render(<ProductionPlansTable plans={mockPlans} onDelete={onDelete} />)

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    await user.click(deleteButtons[0])

    expect(onDelete).toHaveBeenCalledWith(mockPlans[0])
  })

  it('should show loading state', () => {
    render(<ProductionPlansTable plans={[]} isLoading={true} />)

    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })

  it('should display all status badges correctly', () => {
    const plansWithAllStatuses: ProductionPlan[] = [
      { ...mockPlans[0], status: 'DRAFT' },
      { ...mockPlans[0], id: 2, status: 'APPROVED' },
      { ...mockPlans[0], id: 3, status: 'IN_PROGRESS' },
      { ...mockPlans[0], id: 4, status: 'COMPLETED' },
      { ...mockPlans[0], id: 5, status: 'CANCELLED' },
    ]

    render(<ProductionPlansTable plans={plansWithAllStatuses} />)

    expect(screen.getByText('DRAFT')).toHaveClass('status-draft')
    expect(screen.getByText('APPROVED')).toHaveClass('status-approved')
    expect(screen.getByText('IN_PROGRESS')).toHaveClass('status-in-progress')
    expect(screen.getByText('COMPLETED')).toHaveClass('status-completed')
    expect(screen.getByText('CANCELLED')).toHaveClass('status-cancelled')
  })
})
