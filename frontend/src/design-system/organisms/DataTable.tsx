import { useState, useMemo, ReactNode, useId } from 'react'
import { Skeleton } from '../atoms/Skeleton'
import { Checkbox } from '../atoms/Checkbox'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table'
import './DataTable.css'

/**
 * DataTable Organism
 *
 * Production-ready data table with sorting, filtering, pagination, and selection
 * - Single Responsibility: Display and manage tabular data
 * - Accessibility: ARIA grid, keyboard navigation, screen reader support
 * - Features: Sort, filter, paginate, select, loading, empty states
 */

export interface Column<T> {
  header: string
  accessor: keyof T | ((row: T) => any)
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, row: T) => ReactNode
  width?: string
}

export interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  pagination?: boolean
  pageSize?: number
  pageSizeOptions?: number[]
  onRowClick?: (row: T) => void
  emptyState?: ReactNode
  stickyHeader?: boolean
  rowKey?: keyof T | ((row: T) => string | number)
}

export function DataTable<T>({
  data,
  columns,
  loading = false,
  pagination = true,
  pageSize: initialPageSize = 25,
  pageSizeOptions = [10, 25, 50, 100],
  onRowClick,
  emptyState,
  stickyHeader = true,
  rowKey = 'id' as keyof T,
}: DataTableProps<T>) {
  const filterId = useId()
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const [selectedRows, setSelectedRows] = useState<Set<string | number>>(new Set())

  // Get cell value from accessor
  const getCellValue = (row: T, accessor: keyof T | ((row: T) => any)): any => {
    if (typeof accessor === 'function') {
      return accessor(row)
    }
    return row[accessor]
  }

  // Get unique row identifier
  const getRowKey = (row: T, index: number): string | number => {
    if (typeof rowKey === 'function') {
      return rowKey(row)
    }
    const value = row[rowKey]
    if (typeof value === 'string' || typeof value === 'number') {
      return value
    }
    return index
  }

  // Apply filters and sorting
  const processedData = useMemo(() => {
    let result = [...data]

    // Apply filters
    Object.entries(filters).forEach(([columnHeader, filterValue]) => {
      if (filterValue) {
        const column = columns.find(col => col.header === columnHeader)
        if (column) {
          result = result.filter(row => {
            const cellValue = getCellValue(row, column.accessor)
            return String(cellValue).toLowerCase().includes(filterValue.toLowerCase())
          })
        }
      }
    })

    // Apply sorting
    if (sortColumn) {
      const column = columns.find(col => col.header === sortColumn)
      if (column) {
        result.sort((a, b) => {
          const aVal = getCellValue(a, column.accessor)
          const bVal = getCellValue(b, column.accessor)

          let comparison = 0
          if (aVal < bVal) comparison = -1
          if (aVal > bVal) comparison = 1

          return sortDirection === 'asc' ? comparison : -comparison
        })
      }
    }

    return result
  }, [data, filters, sortColumn, sortDirection, columns])

  // Paginate data
  const paginatedData = useMemo(() => {
    if (!pagination) return processedData

    const startIndex = (currentPage - 1) * pageSize
    return processedData.slice(startIndex, startIndex + pageSize)
  }, [processedData, currentPage, pageSize, pagination])

  // Calculate pagination info
  const totalPages = Math.ceil(processedData.length / pageSize)
  const startRow = processedData.length === 0 ? 0 : (currentPage - 1) * pageSize + 1
  const endRow = Math.min(currentPage * pageSize, processedData.length)

  // Handle sort
  const handleSort = (column: Column<T>) => {
    if (!column.sortable) return

    if (sortColumn === column.header) {
      // Toggle direction
      setSortDirection(prev => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      // New column - start with ascending
      setSortColumn(column.header)
      setSortDirection('asc')
    }
  }

  // Handle filter
  const handleFilter = (column: Column<T>, value: string) => {
    setFilters(prev => ({
      ...prev,
      [column.header]: value,
    }))
    setCurrentPage(1) // Reset to first page when filtering
  }

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)))
  }

  // Handle page size change
  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize)
    setCurrentPage(1) // Reset to first page when changing size
  }

  // Handle row selection
  const handleRowSelect = (rowKey: string | number, checked: boolean) => {
    setSelectedRows(prev => {
      const newSet = new Set(prev)
      if (checked) {
        newSet.add(rowKey)
      } else {
        newSet.delete(rowKey)
      }
      return newSet
    })
  }

  // Handle select all
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allKeys = paginatedData.map((row, index) => getRowKey(row, index))
      setSelectedRows(new Set(allKeys))
    } else {
      setSelectedRows(new Set())
    }
  }

  // Check if all visible rows are selected
  const allSelected =
    paginatedData.length > 0 &&
    paginatedData.every((row, index) => selectedRows.has(getRowKey(row, index)))

  const someSelected =
    !allSelected &&
    paginatedData.some((row, index) => selectedRows.has(getRowKey(row, index)))

  // Render cell content
  const renderCell = (column: Column<T>, row: T) => {
    const value = getCellValue(row, column.accessor)

    if (column.render) {
      return column.render(value, row)
    }

    return value
  }

  const containerClasses = [
    'data-table-container',
    stickyHeader && 'data-table--sticky-header',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={containerClasses}>
      <Table className="data-table" role="grid">
        <TableHeader>
          {/* Column headers row */}
          <TableRow role="row">
            <TableHead role="columnheader" className="data-table__select-column">
              <Checkbox
                checked={allSelected}
                indeterminate={someSelected}
                onChange={handleSelectAll}
                aria-label="Select all rows"
              />
            </TableHead>
            {columns.map((column, index) => (
              <TableHead
                key={index}
                role="columnheader"
                style={{ width: column.width }}
                aria-sort={
                  sortColumn === column.header
                    ? sortDirection === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : undefined
                }
              >
                {column.sortable ? (
                  <button
                    className="data-table__sort-button"
                    onClick={() => handleSort(column)}
                    aria-label={`Sort by ${column.header}`}
                  >
                    {column.header}
                    {sortColumn === column.header && (
                      <span className="data-table__sort-icon" role="img" aria-hidden="true">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </button>
                ) : (
                  <span>{column.header}</span>
                )}
              </TableHead>
            ))}
          </TableRow>

          {/* Filter row */}
          <TableRow role="row" className="data-table__filter-row">
            <TableHead role="columnheader"></TableHead>
            {columns.map((column, index) => (
              <TableHead key={index} role="columnheader">
                {column.filterable && (
                  <input
                    type="text"
                    className="data-table__filter-input"
                    placeholder="Filter..."
                    value={filters[column.header] || ''}
                    onChange={e => handleFilter(column, e.target.value)}
                    aria-label={`Filter ${column.header}`}
                    id={`${filterId}-filter-${index}`}
                  />
                )}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>

        <TableBody>
          {loading ? (
            // Loading skeleton
            Array.from({ length: pageSize }).map((_, index) => (
              <TableRow key={index} role="row">
                <TableCell role="gridcell">
                  <Skeleton variant="rectangular" width={20} height={20} />
                </TableCell>
                {columns.map((_, colIndex) => (
                  <TableCell key={colIndex} role="gridcell">
                    <Skeleton variant="text" width="80%" />
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : paginatedData.length === 0 ? (
            // Empty state
            <TableRow role="row">
              <TableCell
                role="gridcell"
                colSpan={columns.length + 1}
                className="data-table__empty"
              >
                {emptyState || <p>No data found.</p>}
              </TableCell>
            </TableRow>
          ) : (
            // Data rows
            paginatedData.map((row, index) => {
              const key = getRowKey(row, index)
              const isSelected = selectedRows.has(key)

              return (
                <TableRow
                  key={key}
                  role="row"
                  className={onRowClick ? 'data-table__row--clickable' : ''}
                  onClick={() => onRowClick?.(row)}
                  aria-selected={isSelected}
                >
                  <TableCell role="gridcell" onClick={e => e.stopPropagation()}>
                    <Checkbox
                      checked={isSelected}
                      onChange={checked => handleRowSelect(key, checked)}
                      aria-label={`Select row ${index + 1}`}
                    />
                  </TableCell>
                  {columns.map((column, colIndex) => (
                    <TableCell key={colIndex} role="gridcell">
                      {renderCell(column, row)}
                    </TableCell>
                  ))}
                </TableRow>
              )
            })
          )}
        </TableBody>
      </Table>

      {pagination && !loading && processedData.length > 0 && (
        <div className="data-table__pagination">
          <div className="data-table__pagination-info">
            Showing {startRow}-{endRow} of {processedData.length}
          </div>

          <div className="data-table__pagination-controls">
            <label htmlFor={`${filterId}-pagesize`} className="data-table__pagesize-label">
              Rows per page:
            </label>
            <select
              id={`${filterId}-pagesize`}
              value={pageSize}
              onChange={e => handlePageSizeChange(Number(e.target.value))}
              className="data-table__pagesize-select"
              aria-label="Rows per page"
            >
              {pageSizeOptions.map(size => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>

            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="data-table__pagination-button"
              aria-label="Previous page"
            >
              Previous
            </button>

            <span className="data-table__pagination-page">
              Page {currentPage} of {totalPages}
            </span>

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="data-table__pagination-button"
              aria-label="Next page"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

DataTable.displayName = 'DataTable'
