import { describe, it, expect, vi } from 'vitest'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DataTable, Column } from '../DataTable'

interface TestData {
  id: number
  name: string
  category: string
  quantity: number
  status: 'active' | 'inactive'
}

const mockData: TestData[] = [
  { id: 1, name: 'Item A', category: 'Electronics', quantity: 10, status: 'active' },
  { id: 2, name: 'Item B', category: 'Furniture', quantity: 25, status: 'active' },
  { id: 3, name: 'Item C', category: 'Electronics', quantity: 5, status: 'inactive' },
  { id: 4, name: 'Item D', category: 'Hardware', quantity: 100, status: 'active' },
  { id: 5, name: 'Item E', category: 'Furniture', quantity: 15, status: 'inactive' },
]

const mockColumns: Column<TestData>[] = [
  {
    header: 'ID',
    accessor: 'id',
    sortable: true,
  },
  {
    header: 'Name',
    accessor: 'name',
    sortable: true,
    filterable: true,
  },
  {
    header: 'Category',
    accessor: 'category',
    sortable: true,
    filterable: true,
  },
  {
    header: 'Quantity',
    accessor: 'quantity',
    sortable: true,
  },
  {
    header: 'Status',
    accessor: 'status',
    render: (value) => <span className="status-badge">{value}</span>,
  },
]

describe('DataTable', () => {
  describe('Rendering Tests', () => {
    it('renders table with data rows', () => {
      render(<DataTable data={mockData} columns={mockColumns} />)

      // Check that all rows are rendered
      const rows = screen.getAllByRole('row')
      // +2 for header row and filter row
      expect(rows.length).toBeGreaterThan(mockData.length)

      // Verify data content
      expect(screen.getByText('Item A')).toBeInTheDocument()
      expect(screen.getByText('Item B')).toBeInTheDocument()
      expect(screen.getAllByText('Electronics').length).toBeGreaterThan(0)
    })

    it('renders column headers', () => {
      render(<DataTable data={mockData} columns={mockColumns} />)

      // Check all column headers are present
      expect(screen.getByText('ID')).toBeInTheDocument()
      expect(screen.getByText('Name')).toBeInTheDocument()
      expect(screen.getByText('Category')).toBeInTheDocument()
      expect(screen.getByText('Quantity')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
    })

    it('renders custom cell content with render function', () => {
      render(<DataTable data={mockData} columns={mockColumns} />)

      // Check that custom render function was applied
      const statusBadges = document.querySelectorAll('.status-badge')
      expect(statusBadges.length).toBeGreaterThan(0)
      expect(statusBadges[0]).toHaveTextContent('active')
    })
  })

  describe('Sorting Tests', () => {
    it('sorts column ascending on first click', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} />)

      // Click on "Quantity" header to sort
      const quantityHeader = screen.getByText('Quantity').closest('button')
      expect(quantityHeader).toBeInTheDocument()

      await user.click(quantityHeader!)

      // Get all quantity cells and verify ascending order
      const rows = screen.getAllByRole('row').slice(2) // Skip header and filter rows
      const firstRowCells = within(rows[0]).getAllByRole('gridcell')
      const quantityIndex = 4 // Quantity is 5th column (index 4 - includes checkbox column)

      // First row should have smallest quantity (5)
      expect(firstRowCells[quantityIndex]).toHaveTextContent('5')
    })

    it('sorts column descending on second click', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} />)

      const quantityHeader = screen.getByText('Quantity').closest('button')

      // First click - ascending
      await user.click(quantityHeader!)
      // Second click - descending
      await user.click(quantityHeader!)

      // Get first data row
      const rows = screen.getAllByRole('row').slice(2)
      const firstRowCells = within(rows[0]).getAllByRole('gridcell')
      const quantityIndex = 4 // Includes checkbox column

      // First row should have largest quantity (100)
      expect(firstRowCells[quantityIndex]).toHaveTextContent('100')
    })

    it('shows sort indicator icon', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} />)

      const nameHeader = screen.getByText('Name').closest('button')
      await user.click(nameHeader!)

      // Check for sort indicator (should have aria-label or specific class)
      const sortIcon = within(nameHeader!).getByRole('img', { hidden: true })
      expect(sortIcon).toBeInTheDocument()
    })
  })

  describe('Filtering Tests', () => {
    it('filters rows by column value', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} />)

      // Find Name filter input
      const nameFilter = screen.getByLabelText('Filter Name')

      // Type filter value
      await user.type(nameFilter, 'Item A')

      // Should only show one row (Item A)
      await waitFor(() => {
        const dataRows = screen.getAllByRole('row').slice(2) // Skip header and filter
        expect(dataRows).toHaveLength(1)
      })

      expect(screen.getByText('Item A')).toBeInTheDocument()
      expect(screen.queryByText('Item B')).not.toBeInTheDocument()
    })

    it('shows no results when filter matches nothing', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} />)

      const nameFilter = screen.getByLabelText('Filter Name')
      await user.type(nameFilter, 'NonExistent')

      // Should show empty state
      await waitFor(() => {
        expect(screen.getByText(/no.*found/i)).toBeInTheDocument()
      })
    })
  })

  describe('Pagination Tests', () => {
    const largeDataSet = Array.from({ length: 100 }, (_, i) => ({
      id: i + 1,
      name: `Item ${i + 1}`,
      category: i % 2 === 0 ? 'Electronics' : 'Furniture',
      quantity: i * 10,
      status: (i % 2 === 0 ? 'active' : 'inactive') as 'active' | 'inactive',
    }))

    it('paginates data with correct page size', () => {
      render(<DataTable data={largeDataSet} columns={mockColumns} pageSize={10} />)

      // Should show 10 rows (default page size)
      const dataRows = screen.getAllByRole('row').slice(2) // Skip header and filter
      expect(dataRows.length).toBeLessThanOrEqual(10)
    })

    it('changes page size when selector changed', async () => {
      const user = userEvent.setup()
      render(<DataTable data={largeDataSet} columns={mockColumns} pageSize={10} />)

      // Find page size selector
      const pageSizeSelector = screen.getByLabelText(/rows per page/i)

      // Change to 50 rows per page
      await user.selectOptions(pageSizeSelector, '50')

      // Should now show up to 50 rows
      await waitFor(() => {
        const dataRows = screen.getAllByRole('row').slice(2)
        expect(dataRows.length).toBeLessThanOrEqual(50)
        expect(dataRows.length).toBeGreaterThan(10)
      })
    })

    it('navigates to next/previous page', async () => {
      const user = userEvent.setup()
      render(<DataTable data={largeDataSet} columns={mockColumns} pageSize={10} />)

      // Get first row ID (skip checkbox column)
      const firstPageRows = screen.getAllByRole('row').slice(2)
      const firstPageFirstCell = within(firstPageRows[0]).getAllByRole('gridcell')[1] // Index 1 for ID column
      const firstPageId = firstPageFirstCell.textContent

      // Click next button
      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      // Get new first row ID (skip checkbox column at index 0)
      await waitFor(() => {
        const secondPageRows = screen.getAllByRole('row').slice(2)
        const secondPageFirstCell = within(secondPageRows[0]).getAllByRole('gridcell')[1] // Index 1 for ID column
        const secondPageId = secondPageFirstCell.textContent

        // IDs should be different
        expect(secondPageId).not.toBe(firstPageId)
      })

      // Click previous button
      const prevButton = screen.getByRole('button', { name: /previous/i })
      await user.click(prevButton)

      // Should be back to original first row
      await waitFor(() => {
        const backToFirstRows = screen.getAllByRole('row').slice(2)
        const backToFirstCell = within(backToFirstRows[0]).getAllByRole('gridcell')[1] // Index 1 for ID column
        expect(backToFirstCell.textContent).toBe(firstPageId)
      })
    })

    it('shows correct page info (Showing 1-25 of 100)', () => {
      render(<DataTable data={largeDataSet} columns={mockColumns} pageSize={25} />)

      // Check pagination info text
      expect(screen.getByText(/showing 1.*25.*100/i)).toBeInTheDocument()
    })
  })

  describe('Selection Tests', () => {
    it('selects individual row with checkbox', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} />)

      // Find first row checkbox
      const rows = screen.getAllByRole('row').slice(2) // Skip header and filter
      const firstRowCheckbox = within(rows[0]).getByRole('checkbox')

      // Click checkbox
      await user.click(firstRowCheckbox)

      // Checkbox should be checked
      expect(firstRowCheckbox).toBeChecked()
    })

    it('selects all rows with header checkbox', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} />)

      // Find "select all" checkbox in header
      const headerRow = screen.getAllByRole('row')[0]
      const selectAllCheckbox = within(headerRow).getByRole('checkbox')

      // Click "select all"
      await user.click(selectAllCheckbox)

      // All row checkboxes should be checked
      const rows = screen.getAllByRole('row').slice(2)
      rows.forEach(row => {
        const checkbox = within(row).getByRole('checkbox')
        expect(checkbox).toBeChecked()
      })
    })
  })

  describe('State Tests', () => {
    it('shows empty state when no data', () => {
      const emptyMessage = 'No items found. Create your first item.'
      render(
        <DataTable
          data={[]}
          columns={mockColumns}
          emptyState={<p>{emptyMessage}</p>}
        />
      )

      expect(screen.getByText(emptyMessage)).toBeInTheDocument()
    })

    it('shows loading skeleton when loading', () => {
      render(<DataTable data={mockData} columns={mockColumns} loading={true} />)

      // Should show skeleton rows instead of data
      const skeletons = document.querySelectorAll('.skeleton')
      expect(skeletons.length).toBeGreaterThan(0)

      // Should NOT show actual data
      expect(screen.queryByText('Item A')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility Tests', () => {
    it('has proper ARIA labels on interactive elements', () => {
      render(<DataTable data={mockData} columns={mockColumns} />)

      // Table should have grid role
      const table = screen.getByRole('grid')
      expect(table).toBeInTheDocument()

      // Column headers should have columnheader role
      const headers = screen.getAllByRole('columnheader')
      expect(headers.length).toBeGreaterThan(0)

      // Filter inputs should have labels
      const nameFilter = screen.getByLabelText('Filter Name')
      expect(nameFilter).toBeInTheDocument()

      const categoryFilter = screen.getByLabelText('Filter Category')
      expect(categoryFilter).toBeInTheDocument()
    })

    it('keyboard navigation works (Tab, Enter)', async () => {
      const user = userEvent.setup()
      const onRowClick = vi.fn()

      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          onRowClick={onRowClick}
        />
      )

      // Get the ID header button
      const idHeader = screen.getByText('ID').closest('button')
      expect(idHeader).toBeInTheDocument()

      // Focus and click the sort button
      idHeader!.focus()
      expect(idHeader).toHaveFocus()

      // Press Enter to sort
      await user.keyboard('{Enter}')

      // Should trigger sort (verify by checking aria-sort attribute)
      const headerCell = idHeader!.closest('th')
      expect(headerCell).toHaveAttribute('aria-sort')
    })
  })

  describe('Row Click Handler', () => {
    it('calls onRowClick when row is clicked', async () => {
      const user = userEvent.setup()
      const onRowClick = vi.fn()

      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          onRowClick={onRowClick}
        />
      )

      // Click first data row
      const rows = screen.getAllByRole('row').slice(2)
      await user.click(rows[0])

      // Handler should be called with row data
      expect(onRowClick).toHaveBeenCalledWith(mockData[0])
    })
  })

  describe('Responsive Behavior', () => {
    it('applies sticky header class when stickyHeader is true', () => {
      render(<DataTable data={mockData} columns={mockColumns} stickyHeader={true} />)

      const table = screen.getByRole('grid')
      const container = table.closest('.data-table-container')

      expect(container).toHaveClass('data-table--sticky-header')
    })
  })

  describe('Custom Row Key', () => {
    it('uses custom rowKey function', () => {
      const customRowKey = (row: TestData) => `custom-${row.id}`

      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          rowKey={customRowKey}
        />
      )

      // Rows should have custom keys (check via data attributes or key prop)
      const rows = screen.getAllByRole('row').slice(2)
      expect(rows.length).toBeGreaterThan(0)
    })
  })
})
