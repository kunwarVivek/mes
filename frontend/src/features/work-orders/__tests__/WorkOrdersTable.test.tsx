/**
 * WorkOrdersTable Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WorkOrdersTable } from '../components/WorkOrdersTable'
import type { WorkOrder } from '../types/workOrder.types'

const mockWorkOrders: WorkOrder[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    work_order_number: 'WO001',
    material_id: 1,
    order_type: 'PRODUCTION',
    order_status: 'IN_PROGRESS',
    planned_quantity: 100,
    actual_quantity: 50,
    start_date_planned: '2024-01-15',
    end_date_planned: '2024-01-20',
    priority: 7,
    created_by_user_id: 1,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    work_order_number: 'WO002',
    material_id: 2,
    order_type: 'REWORK',
    order_status: 'PLANNED',
    planned_quantity: 50,
    actual_quantity: 0,
    start_date_planned: '2024-02-01',
    end_date_planned: '2024-02-10',
    priority: 9,
    created_by_user_id: 1,
    created_at: '2024-01-02T00:00:00Z',
  },
]

describe('WorkOrdersTable', () => {
  it('should render table with work orders', () => {
    render(<WorkOrdersTable workOrders={mockWorkOrders} />)

    expect(screen.getByText('WO001')).toBeInTheDocument()
    expect(screen.getByText('WO002')).toBeInTheDocument()
    expect(screen.getByText('PRODUCTION')).toBeInTheDocument()
    expect(screen.getByText('REWORK')).toBeInTheDocument()
  })

  it('should display status badges with correct colors', () => {
    render(<WorkOrdersTable workOrders={mockWorkOrders} />)

    const inProgressBadge = screen.getByText('IN_PROGRESS')
    const plannedBadge = screen.getByText('PLANNED')

    expect(inProgressBadge).toHaveClass('status-badge-in-progress')
    expect(plannedBadge).toHaveClass('status-badge-planned')
  })

  it('should display priority badges with correct colors', () => {
    render(<WorkOrdersTable workOrders={mockWorkOrders} />)

    const highBadge = screen.getByText('HIGH')
    const criticalBadge = screen.getByText('CRITICAL')

    expect(highBadge).toHaveClass('priority-badge-high')
    expect(criticalBadge).toHaveClass('priority-badge-critical')
  })

  it('should calculate and display progress percentage', () => {
    render(<WorkOrdersTable workOrders={mockWorkOrders} />)

    expect(screen.getByText('50%')).toBeInTheDocument()
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('should call onEdit when edit button clicked', async () => {
    const onEdit = vi.fn()
    const user = userEvent.setup()

    render(<WorkOrdersTable workOrders={mockWorkOrders} onEdit={onEdit} />)

    const editButtons = screen.getAllByRole('button', { name: /Edit/i })
    await user.click(editButtons[0])

    expect(onEdit).toHaveBeenCalledWith(mockWorkOrders[0])
  })

  it('should call onDelete when delete button clicked', async () => {
    const onDelete = vi.fn()
    const user = userEvent.setup()

    render(<WorkOrdersTable workOrders={mockWorkOrders} onDelete={onDelete} />)

    const deleteButtons = screen.getAllByRole('button', { name: /Delete/i })
    await user.click(deleteButtons[0])

    expect(onDelete).toHaveBeenCalledWith(1)
  })

  it('should render empty state when no work orders', () => {
    render(<WorkOrdersTable workOrders={[]} />)

    expect(screen.getByText(/No work orders found/i)).toBeInTheDocument()
  })

  it('should render loading state', () => {
    render(<WorkOrdersTable workOrders={[]} isLoading={true} />)

    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })
})
