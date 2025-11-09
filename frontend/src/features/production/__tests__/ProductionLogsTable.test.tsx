/**
 * ProductionLogsTable Component Tests
 *
 * TDD: Testing table display with pagination and yield rate coloring
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProductionLogsTable } from '../components/ProductionLogsTable'
import type { ProductionLog } from '../types/productionLog.types'

describe('ProductionLogsTable', () => {
  const mockLogs: ProductionLog[] = [
    {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      work_order_id: 10,
      timestamp: '2025-01-15T14:30:00Z',
      quantity_produced: 100,
      quantity_scrapped: 2,
      quantity_reworked: 1,
      operator_id: 3,
      shift_id: 1,
      notes: 'Good run',
    },
    {
      id: 2,
      organization_id: 1,
      plant_id: 1,
      work_order_id: 10,
      timestamp: '2025-01-15T16:00:00Z',
      quantity_produced: 50,
      quantity_scrapped: 10,
      quantity_reworked: 5,
      operator_id: 3,
      shift_id: 1,
      notes: 'Issues encountered',
    },
  ]

  const defaultProps = {
    logs: mockLogs,
    isLoading: false,
    page: 1,
    pageSize: 50,
    total: 2,
    onPageChange: vi.fn(),
  }

  it('should render table with log data', () => {
    render(<ProductionLogsTable {...defaultProps} />)
    expect(screen.getByText('Good run')).toBeInTheDocument()
    expect(screen.getByText('Issues encountered')).toBeInTheDocument()
  })

  it('should display formatted timestamps', () => {
    render(<ProductionLogsTable {...defaultProps} />)
    // Should format as local date/time
    const timestamps = screen.getAllByText(/Jan 15, 2025/)
    expect(timestamps.length).toBeGreaterThan(0)
  })

  it('should display quantity values', () => {
    render(<ProductionLogsTable {...defaultProps} />)
    expect(screen.getByText('100')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
  })

  it('should calculate and display yield rate', () => {
    render(<ProductionLogsTable {...defaultProps} />)
    // First log: 100 / (100 + 2 + 1) = 97.1%
    expect(screen.getByText('97.1%')).toBeInTheDocument()
    // Second log: 50 / (50 + 10 + 5) = 76.9%
    expect(screen.getByText('76.9%')).toBeInTheDocument()
  })

  it('should show loading skeleton when isLoading is true', () => {
    const { container } = render(<ProductionLogsTable {...defaultProps} isLoading={true} />)
    const skeletons = container.querySelectorAll('.skeleton')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('should show empty state when no logs', () => {
    render(<ProductionLogsTable {...defaultProps} logs={[]} />)
    expect(screen.getByText(/no production logs/i)).toBeInTheDocument()
  })

  it('should call onPageChange when page button clicked', async () => {
    const user = userEvent.setup()
    const onPageChange = vi.fn()

    render(
      <ProductionLogsTable
        {...defaultProps}
        page={1}
        total={100}
        onPageChange={onPageChange}
      />
    )

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    expect(onPageChange).toHaveBeenCalledWith(2)
  })
})
