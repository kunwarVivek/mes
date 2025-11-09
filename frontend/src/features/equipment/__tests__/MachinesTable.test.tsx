/**
 * MachinesTable Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MachinesTable } from '../components/MachinesTable'
import type { Machine } from '../types/machine.types'

const mockMachines: Machine[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    machine_code: 'CNC001',
    machine_name: 'CNC Machine 1',
    description: 'High-precision CNC',
    work_center_id: 1,
    status: 'AVAILABLE',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    machine_code: 'PRESS001',
    machine_name: 'Hydraulic Press',
    description: 'Heavy-duty press',
    work_center_id: 2,
    status: 'RUNNING',
    is_active: true,
    created_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 3,
    organization_id: 1,
    plant_id: 1,
    machine_code: 'MILL001',
    machine_name: 'Milling Machine',
    description: 'CNC milling',
    work_center_id: 1,
    status: 'DOWN',
    is_active: false,
    created_at: '2024-01-03T00:00:00Z',
  },
]

describe('MachinesTable', () => {
  it('should render loading skeleton when loading', () => {
    render(<MachinesTable machines={[]} isLoading={true} />)

    expect(screen.queryByText('No machines found')).not.toBeInTheDocument()
  })

  it('should render empty state when no machines', () => {
    render(<MachinesTable machines={[]} isLoading={false} />)

    expect(screen.getByText('No machines found')).toBeInTheDocument()
  })

  it('should render machines table with data', () => {
    render(<MachinesTable machines={mockMachines} />)

    expect(screen.getByText('CNC001')).toBeInTheDocument()
    expect(screen.getByText('CNC Machine 1')).toBeInTheDocument()
    expect(screen.getByText('PRESS001')).toBeInTheDocument()
    expect(screen.getByText('Hydraulic Press')).toBeInTheDocument()
  })

  it('should call onEdit when edit button clicked', async () => {
    const onEdit = vi.fn()
    const user = userEvent.setup()

    render(<MachinesTable machines={mockMachines} onEdit={onEdit} />)

    const editButtons = screen.getAllByText('Edit')
    await user.click(editButtons[0])

    expect(onEdit).toHaveBeenCalledWith(mockMachines[0])
  })

  it('should call onDelete when delete button clicked', async () => {
    const onDelete = vi.fn()
    const user = userEvent.setup()

    render(<MachinesTable machines={mockMachines} onDelete={onDelete} />)

    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    expect(onDelete).toHaveBeenCalledWith(mockMachines[0])
  })

  it('should call onRowClick when row clicked', async () => {
    const onRowClick = vi.fn()
    const user = userEvent.setup()

    render(<MachinesTable machines={mockMachines} onRowClick={onRowClick} />)

    const row = screen.getByText('CNC Machine 1').closest('tr')
    await user.click(row!)

    expect(onRowClick).toHaveBeenCalledWith(mockMachines[0])
  })

  it('should display status badges with correct colors', () => {
    render(<MachinesTable machines={mockMachines} />)

    const availableBadge = screen.getByText('AVAILABLE')
    const runningBadge = screen.getByText('RUNNING')
    const downBadge = screen.getByText('DOWN')

    expect(availableBadge).toBeInTheDocument()
    expect(runningBadge).toBeInTheDocument()
    expect(downBadge).toBeInTheDocument()

    // Check CSS classes for colors
    expect(availableBadge).toHaveClass('status-available')
    expect(runningBadge).toHaveClass('status-running')
    expect(downBadge).toHaveClass('status-down')
  })

  it('should display active/inactive status correctly', () => {
    render(<MachinesTable machines={mockMachines} />)

    // Two machines are active
    const rows = screen.getAllByRole('row')
    expect(rows.length).toBeGreaterThan(1) // At least header + data rows

    // One machine is inactive
    const inactiveElement = screen.getByText('Inactive')
    expect(inactiveElement).toBeInTheDocument()
  })

  it('should show pulse animation for RUNNING status', () => {
    render(<MachinesTable machines={mockMachines} />)

    const runningBadge = screen.getByText('RUNNING')
    expect(runningBadge).toHaveClass('status-pulse')
  })

  it('should handle onStatusChange callback', async () => {
    const onStatusChange = vi.fn()
    const user = userEvent.setup()

    render(<MachinesTable machines={mockMachines} onStatusChange={onStatusChange} />)

    const statusButtons = screen.getAllByText('Change Status')
    await user.click(statusButtons[0])

    expect(onStatusChange).toHaveBeenCalledWith(mockMachines[0])
  })

  it('should display all machine columns', () => {
    render(<MachinesTable machines={mockMachines} />)

    expect(screen.getByText('Machine Code')).toBeInTheDocument()
    expect(screen.getByText('Machine Name')).toBeInTheDocument()
    expect(screen.getByText('Description')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: /active/i })).toBeInTheDocument()
    expect(screen.getByText('Actions')).toBeInTheDocument()
  })
})
