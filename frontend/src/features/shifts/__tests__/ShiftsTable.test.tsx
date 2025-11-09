/**
 * ShiftsTable Component Tests
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ShiftsTable } from '../components/ShiftsTable'
import type { Shift } from '../types/shift.types'

const mockShifts: Shift[] = [
  {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    shift_code: 'A',
    shift_name: 'Morning Shift',
    start_time: '06:00:00',
    end_time: '14:00:00',
    production_target: 1000,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    organization_id: 1,
    plant_id: 1,
    shift_code: 'B',
    shift_name: 'Afternoon Shift',
    start_time: '14:00:00',
    end_time: '22:00:00',
    production_target: 900,
    is_active: true,
    created_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 3,
    organization_id: 1,
    plant_id: 1,
    shift_code: 'C',
    shift_name: 'Night Shift',
    start_time: '22:00:00',
    end_time: '06:00:00',
    production_target: 800,
    is_active: false,
    created_at: '2024-01-03T00:00:00Z',
  },
]

describe('ShiftsTable', () => {
  it('should render loading skeleton when loading', () => {
    render(<ShiftsTable shifts={[]} isLoading={true} />)

    expect(screen.queryByText('No shifts found')).not.toBeInTheDocument()
  })

  it('should render empty state when no shifts', () => {
    render(<ShiftsTable shifts={[]} isLoading={false} />)

    expect(screen.getByText('No shifts found')).toBeInTheDocument()
  })

  it('should render shifts table with data', () => {
    render(<ShiftsTable shifts={mockShifts} />)

    expect(screen.getByText('A')).toBeInTheDocument()
    expect(screen.getByText('Morning Shift')).toBeInTheDocument()
    expect(screen.getByText('B')).toBeInTheDocument()
    expect(screen.getByText('Afternoon Shift')).toBeInTheDocument()
    expect(screen.getByText('C')).toBeInTheDocument()
    expect(screen.getByText('Night Shift')).toBeInTheDocument()
  })

  it('should display time range correctly', () => {
    render(<ShiftsTable shifts={mockShifts} />)

    expect(screen.getByText('06:00:00 - 14:00:00')).toBeInTheDocument()
    expect(screen.getByText('14:00:00 - 22:00:00')).toBeInTheDocument()
    expect(screen.getByText('22:00:00 - 06:00:00')).toBeInTheDocument()
  })

  it('should display production targets', () => {
    render(<ShiftsTable shifts={mockShifts} />)

    expect(screen.getByText('1000')).toBeInTheDocument()
    expect(screen.getByText('900')).toBeInTheDocument()
    expect(screen.getByText('800')).toBeInTheDocument()
  })

  it('should call onEdit when edit button clicked', async () => {
    const onEdit = vi.fn()
    const user = userEvent.setup()

    render(<ShiftsTable shifts={mockShifts} onEdit={onEdit} />)

    const editButtons = screen.getAllByText('Edit')
    await user.click(editButtons[0])

    expect(onEdit).toHaveBeenCalledWith(mockShifts[0])
  })

  it('should call onRowClick when row clicked', async () => {
    const onRowClick = vi.fn()
    const user = userEvent.setup()

    render(<ShiftsTable shifts={mockShifts} onRowClick={onRowClick} />)

    const row = screen.getByText('Morning Shift').closest('tr')
    await user.click(row!)

    expect(onRowClick).toHaveBeenCalledWith(mockShifts[0])
  })

  it('should display status badges correctly', () => {
    render(<ShiftsTable shifts={mockShifts} />)

    const activeBadges = screen.getAllByText('Active')
    expect(activeBadges).toHaveLength(2)
    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })
})
