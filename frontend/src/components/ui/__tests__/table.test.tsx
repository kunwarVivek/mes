import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '../table'

describe('Table', () => {
  it('renders table structure correctly', () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Item 1</TableCell>
            <TableCell>Active</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Item 1')).toBeInTheDocument()
  })

  it('applies custom className to Table', () => {
    const { container } = render(
      <Table className="custom-table">
        <TableBody>
          <TableRow>
            <TableCell>Test</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    const wrapper = container.querySelector('.custom-table')?.parentElement
    expect(wrapper).toBeInTheDocument()
  })

  it('supports data attributes on TableRow', () => {
    render(
      <Table>
        <TableBody>
          <TableRow data-state="selected">
            <TableCell>Selected Row</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    const row = screen.getByText('Selected Row').closest('tr')
    expect(row).toHaveAttribute('data-state', 'selected')
  })

  it('renders empty table', () => {
    const { container } = render(
      <Table>
        <TableBody />
      </Table>
    )

    const table = container.querySelector('table')
    expect(table).toBeInTheDocument()
  })
})
