/**
 * MachineStatusCard Component Tests
 *
 * Tests for real-time machine status display card
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MachineStatusCard } from '../components/MachineStatusCard'
import type { Machine } from '../types/machine.types'

const mockMachine: Machine = {
  id: 1,
  organization_id: 1,
  plant_id: 1,
  machine_code: 'CNC001',
  machine_name: 'CNC Machine 1',
  description: 'High-precision CNC',
  work_center_id: 1,
  status: 'RUNNING',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
}

describe('MachineStatusCard', () => {
  it('should render machine information', () => {
    render(<MachineStatusCard machine={mockMachine} />)

    expect(screen.getByText('CNC001')).toBeInTheDocument()
    expect(screen.getByText('CNC Machine 1')).toBeInTheDocument()
    expect(screen.getByText('RUNNING')).toBeInTheDocument()
  })

  it('should display AVAILABLE status with green badge', () => {
    const machine = { ...mockMachine, status: 'AVAILABLE' as const }
    render(<MachineStatusCard machine={machine} />)

    const statusBadge = screen.getByText('AVAILABLE')
    expect(statusBadge).toHaveClass('status-available')
  })

  it('should display RUNNING status with blue badge and pulse animation', () => {
    render(<MachineStatusCard machine={mockMachine} />)

    const statusBadge = screen.getByText('RUNNING')
    expect(statusBadge).toHaveClass('status-running')
    expect(statusBadge).toHaveClass('status-pulse')
  })

  it('should display DOWN status with red badge', () => {
    const machine = { ...mockMachine, status: 'DOWN' as const }
    render(<MachineStatusCard machine={machine} />)

    const statusBadge = screen.getByText('DOWN')
    expect(statusBadge).toHaveClass('status-down')
  })

  it('should display MAINTENANCE status with yellow badge', () => {
    const machine = { ...mockMachine, status: 'MAINTENANCE' as const }
    render(<MachineStatusCard machine={machine} />)

    const statusBadge = screen.getByText('MAINTENANCE')
    expect(statusBadge).toHaveClass('status-maintenance')
  })

  it('should display SETUP status with gray badge', () => {
    const machine = { ...mockMachine, status: 'SETUP' as const }
    render(<MachineStatusCard machine={machine} />)

    const statusBadge = screen.getByText('SETUP')
    expect(statusBadge).toHaveClass('status-setup')
  })

  it('should display IDLE status correctly', () => {
    const machine = { ...mockMachine, status: 'IDLE' as const }
    render(<MachineStatusCard machine={machine} />)

    const statusBadge = screen.getByText('IDLE')
    expect(statusBadge).toHaveClass('status-idle')
  })

  it('should call onClick when card is clicked', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()

    render(<MachineStatusCard machine={mockMachine} onClick={onClick} />)

    const card = screen.getByText('CNC Machine 1').closest('.machine-status-card')
    await user.click(card!)

    expect(onClick).toHaveBeenCalledWith(mockMachine)
  })

  it('should call onStatusChange when change status button clicked', async () => {
    const onStatusChange = vi.fn()
    const user = userEvent.setup()

    render(<MachineStatusCard machine={mockMachine} onStatusChange={onStatusChange} />)

    const changeButton = screen.getByText('Change Status')
    await user.click(changeButton)

    expect(onStatusChange).toHaveBeenCalledWith(mockMachine)
  })

  it('should display inactive badge for inactive machines', () => {
    const machine = { ...mockMachine, is_active: false }
    render(<MachineStatusCard machine={machine} />)

    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })

  it('should not display inactive badge for active machines', () => {
    render(<MachineStatusCard machine={mockMachine} />)

    expect(screen.queryByText('Inactive')).not.toBeInTheDocument()
  })

  it('should render compact mode when specified', () => {
    render(<MachineStatusCard machine={mockMachine} compact={true} />)

    const card = screen.getByText('CNC Machine 1').closest('.machine-status-card')
    expect(card).toHaveClass('compact')
  })

  it('should show loading state when specified', () => {
    render(<MachineStatusCard machine={mockMachine} isLoading={true} />)

    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument()
  })
})
