/**
 * ShiftsTable Component
 *
 * Table for displaying shifts with actions (edit)
 */
import { Button, Badge, Skeleton } from '@/design-system/atoms'
import { EmptyState } from '@/design-system/molecules'
import type { Shift } from '../types/shift.types'
import './ShiftsTable.css'

export interface ShiftsTableProps {
  shifts: Shift[]
  isLoading?: boolean
  onEdit?: (shift: Shift) => void
  onRowClick?: (shift: Shift) => void
}

export const ShiftsTable = ({
  shifts,
  isLoading,
  onEdit,
  onRowClick,
}: ShiftsTableProps) => {
  if (isLoading) {
    return (
      <div className="shifts-table-skeleton">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} height="48px" />
        ))}
      </div>
    )
  }

  if (shifts.length === 0) {
    return (
      <EmptyState
        title="No shifts found"
        description="No shifts match your filters. Try adjusting your search criteria."
      />
    )
  }

  return (
    <div className="shifts-table-container">
      <table className="shifts-table">
        <thead>
          <tr>
            <th>Shift Code</th>
            <th>Shift Name</th>
            <th>Time Range</th>
            <th>Production Target</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {shifts.map((shift) => (
            <tr
              key={shift.id}
              onClick={() => onRowClick?.(shift)}
              className={onRowClick ? 'shifts-table-row-clickable' : ''}
            >
              <td className="shifts-table-cell-code">{shift.shift_code}</td>
              <td>{shift.shift_name}</td>
              <td>{`${shift.start_time} - ${shift.end_time}`}</td>
              <td>{shift.production_target}</td>
              <td>
                <Badge variant={shift.is_active ? 'success' : 'danger'} size="sm">
                  {shift.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </td>
              <td className="shifts-table-actions">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEdit?.(shift)
                  }}
                >
                  Edit
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
