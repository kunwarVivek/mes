import { ReactNode, HTMLAttributes } from 'react'

/**
 * Table Components
 *
 * Semantic HTML table with consistent styling:
 * - Table (wrapper)
 * - TableHeader (thead)
 * - TableBody (tbody)
 * - TableRow (tr)
 * - TableHead (th)
 * - TableCell (td)
 */

interface TableProps extends HTMLAttributes<HTMLTableElement> {
  children: ReactNode
  className?: string
}

export function Table({ children, className = '', ...props }: TableProps) {
  return (
    <div className="w-full overflow-auto">
      <table className={`w-full border-collapse ${className}`} {...props}>
        {children}
      </table>
    </div>
  )
}

interface TableHeaderProps extends HTMLAttributes<HTMLTableSectionElement> {
  children: ReactNode
  className?: string
}

export function TableHeader({ children, className = '', ...props }: TableHeaderProps) {
  return (
    <thead className={`border-b bg-gray-50 ${className}`} {...props}>
      {children}
    </thead>
  )
}

interface TableBodyProps extends HTMLAttributes<HTMLTableSectionElement> {
  children: ReactNode
  className?: string
}

export function TableBody({ children, className = '', ...props }: TableBodyProps) {
  return (
    <tbody className={className} {...props}>
      {children}
    </tbody>
  )
}

interface TableRowProps extends HTMLAttributes<HTMLTableRowElement> {
  children: ReactNode
  className?: string
}

export function TableRow({ children, className = '', ...props }: TableRowProps) {
  return (
    <tr className={`border-b last:border-0 ${className}`} {...props}>
      {children}
    </tr>
  )
}

interface TableHeadProps extends HTMLAttributes<HTMLTableCellElement> {
  children: ReactNode
  className?: string
}

export function TableHead({ children, className = '', ...props }: TableHeadProps) {
  return (
    <th
      className={`px-4 py-3 text-left text-sm font-semibold text-gray-700 ${className}`}
      {...props}
    >
      {children}
    </th>
  )
}

interface TableCellProps extends HTMLAttributes<HTMLTableCellElement> {
  children: ReactNode
  className?: string
}

export function TableCell({ children, className = '', ...props }: TableCellProps) {
  return (
    <td className={`px-4 py-3 text-sm text-gray-900 ${className}`} {...props}>
      {children}
    </td>
  )
}
