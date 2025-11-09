/**
 * WorkOrdersTable Component
 *
 * Table for displaying work orders with status badges, priority indicators, and actions
 */
import { Button, Badge } from '@/design-system/atoms'
import { EmptyState } from '@/design-system/molecules'
import type { WorkOrder } from '../types/workOrder.types'
import './WorkOrdersTable.css'

export interface WorkOrdersTableProps {
  workOrders: WorkOrder[]
  isLoading?: boolean
  onEdit?: (workOrder: WorkOrder) => void
  onDelete?: (id: number) => void
  onRowClick?: (workOrder: WorkOrder) => void
}

const getStatusBadgeVariant = (status: string): 'success' | 'warning' | 'info' | 'error' | 'neutral' => {
  switch (status) {
    case 'COMPLETED':
      return 'success'
    case 'IN_PROGRESS':
      return 'warning'
    case 'RELEASED':
      return 'info'
    case 'CANCELLED':
      return 'error'
    case 'PLANNED':
    default:
      return 'neutral'
  }
}

const getPriorityBadgeVariant = (priority: number): 'success' | 'warning' | 'info' | 'error' | 'neutral' => {
  if (priority >= 8) return 'error' // CRITICAL
  if (priority >= 6) return 'warning' // HIGH
  if (priority >= 4) return 'info' // MEDIUM
  return 'neutral' // LOW
}

const calculateProgress = (completed: number, planned: number): number => {
  if (planned === 0) return 0
  return Math.round((completed / planned) * 100)
}

export const WorkOrdersTable = ({
  workOrders,
  isLoading,
  onEdit,
  onDelete,
  onRowClick,
}: WorkOrdersTableProps) => {
  if (isLoading) {
    return (
      <div className="work-orders-table-skeleton">
        <div>Loading...</div>
      </div>
    )
  }

  if (workOrders.length === 0) {
    return (
      <EmptyState
        title="No work orders found"
        description="No work orders match your filters. Try adjusting your search criteria."
      />
    )
  }

  return (
    <div className="work-orders-table-container">
      <table className="work-orders-table">
        <thead>
          <tr>
            <th>WO Number</th>
            <th>Type</th>
            <th>Material ID</th>
            <th>Quantity</th>
            <th>Progress</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {workOrders.map((wo) => (
            <tr
              key={wo.id}
              onClick={() => onRowClick?.(wo)}
              className={onRowClick ? 'work-orders-table-row-clickable' : ''}
            >
              <td className="work-orders-table-cell-code">{wo.work_order_number}</td>
              <td>{wo.order_type}</td>
              <td>{wo.material_id}</td>
              <td>
                {wo.actual_quantity} / {wo.planned_quantity}
              </td>
              <td>{calculateProgress(wo.actual_quantity, wo.planned_quantity)}%</td>
              <td>
                <Badge
                  variant={getStatusBadgeVariant(wo.order_status)}
                  size="sm"
                  className={`status-badge-${wo.order_status?.toLowerCase().replace(/_/g, '-') || 'planned'}`}
                >
                  {wo.order_status}
                </Badge>
              </td>
              <td>
                <Badge
                  variant={getPriorityBadgeVariant(wo.priority)}
                  size="sm"
                  className={`priority-badge-${wo.priority >= 8 ? 'critical' : wo.priority >= 6 ? 'high' : wo.priority >= 4 ? 'medium' : 'low'}`}
                >
                  {wo.priority >= 8 ? 'CRITICAL' : wo.priority >= 6 ? 'HIGH' : wo.priority >= 4 ? 'MEDIUM' : 'LOW'}
                </Badge>
              </td>
              <td>{wo.start_date_planned ? new Date(wo.start_date_planned).toLocaleDateString() : '-'}</td>
              <td>{wo.end_date_planned ? new Date(wo.end_date_planned).toLocaleDateString() : '-'}</td>
              <td className="work-orders-table-actions">
                {onEdit && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onEdit(wo)
                    }}
                  >
                    Edit
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDelete(wo.id)
                    }}
                  >
                    Delete
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
