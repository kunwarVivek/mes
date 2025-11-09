/**
 * ProductionPlansTable Component
 *
 * Table for displaying production plans with actions (edit, delete)
 */
import { Button, Badge, Skeleton } from '@/design-system/atoms'
import { EmptyState } from '@/design-system/molecules'
import type { ProductionPlan } from '../types/production.types'
import './ProductionPlansTable.css'

export interface ProductionPlansTableProps {
  plans: ProductionPlan[]
  isLoading?: boolean
  onEdit?: (plan: ProductionPlan) => void
  onDelete?: (plan: ProductionPlan) => void
  onRowClick?: (plan: ProductionPlan) => void
}

export const ProductionPlansTable = ({
  plans,
  isLoading,
  onEdit,
  onDelete,
  onRowClick,
}: ProductionPlansTableProps) => {
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return 'secondary'
      case 'APPROVED':
        return 'primary'
      case 'IN_PROGRESS':
        return 'warning'
      case 'COMPLETED':
        return 'success'
      case 'CANCELLED':
        return 'danger'
      default:
        return 'secondary'
    }
  }

  const getStatusClassName = (status: string) => {
    return `status-${status.toLowerCase().replace('_', '-')}`
  }

  if (isLoading) {
    return (
      <div className="production-plans-table-skeleton">
        <p>Loading...</p>
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} height="48px" />
        ))}
      </div>
    )
  }

  if (plans.length === 0) {
    return (
      <EmptyState
        title="No production plans found"
        description="No production plans match your filters. Try adjusting your search criteria."
      />
    )
  }

  return (
    <div className="production-plans-table-container">
      <table className="production-plans-table">
        <thead>
          <tr>
            <th>Plan Code</th>
            <th>Plan Name</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {plans.map((plan) => (
            <tr
              key={plan.id}
              onClick={() => onRowClick?.(plan)}
              className={onRowClick ? 'production-plans-table-row-clickable' : ''}
            >
              <td className="production-plans-table-cell-code">{plan.plan_code}</td>
              <td>{plan.plan_name}</td>
              <td>{plan.start_date}</td>
              <td>{plan.end_date}</td>
              <td>
                <Badge
                  variant={getStatusBadgeVariant(plan.status)}
                  size="sm"
                  className={getStatusClassName(plan.status)}
                >
                  {plan.status}
                </Badge>
              </td>
              <td className="production-plans-table-actions">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEdit?.(plan)
                  }}
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete?.(plan)
                  }}
                >
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
