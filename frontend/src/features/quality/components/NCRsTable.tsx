/**
 * NCRsTable Component
 *
 * Table for displaying NCRs with status badges and actions
 */
import { Button, Badge, Skeleton } from '@/design-system/atoms'
import { EmptyState } from '@/design-system/molecules'
import type { NCR, NCRStatus, DefectType } from '../types/quality.types'
import './NCRsTable.css'

export interface NCRsTableProps {
  ncrs: NCR[]
  isLoading?: boolean
  onReview?: (ncr: NCR) => void
  onResolve?: (ncr: NCR) => void
  onDelete?: (ncr: NCR) => void
  onRowClick?: (ncr: NCR) => void
}

const getStatusVariant = (status: NCRStatus): 'warning' | 'info' | 'success' | 'default' => {
  switch (status) {
    case 'OPEN':
      return 'warning'
    case 'IN_REVIEW':
      return 'info'
    case 'RESOLVED':
      return 'success'
    case 'CLOSED':
      return 'default'
    default:
      return 'default'
  }
}

const getDefectTypeVariant = (
  defectType: DefectType
): 'primary' | 'secondary' | 'warning' | 'danger' | 'info' => {
  switch (defectType) {
    case 'DIMENSIONAL':
      return 'primary'
    case 'VISUAL':
      return 'secondary'
    case 'FUNCTIONAL':
      return 'danger'
    case 'MATERIAL':
      return 'warning'
    case 'OTHER':
      return 'info'
    default:
      return 'info'
  }
}

export const NCRsTable = ({
  ncrs,
  isLoading,
  onReview,
  onResolve,
  onDelete,
  onRowClick,
}: NCRsTableProps) => {
  if (isLoading) {
    return (
      <div className="ncrs-table-skeleton">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} height="48px" />
        ))}
      </div>
    )
  }

  if (ncrs.length === 0) {
    return (
      <EmptyState
        title="No NCRs found"
        description="No non-conformance reports match your filters. Try adjusting your search criteria."
      />
    )
  }

  return (
    <div className="ncrs-table-container">
      <table className="ncrs-table">
        <thead>
          <tr>
            <th>NCR Number</th>
            <th>Work Order</th>
            <th>Material</th>
            <th>Defect Type</th>
            <th>Description</th>
            <th>Qty Defective</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {ncrs.map((ncr) => (
            <tr
              key={ncr.id}
              onClick={() => onRowClick?.(ncr)}
              className={onRowClick ? 'ncrs-table-row-clickable' : ''}
            >
              <td className="ncrs-table-cell-code">{ncr.ncr_number}</td>
              <td>{ncr.work_order_id}</td>
              <td>{ncr.material_id}</td>
              <td>
                <Badge variant={getDefectTypeVariant(ncr.defect_type)} size="sm">
                  {ncr.defect_type}
                </Badge>
              </td>
              <td className="ncrs-table-cell-description">
                {ncr.defect_description.length > 50
                  ? `${ncr.defect_description.substring(0, 50)}...`
                  : ncr.defect_description}
              </td>
              <td>{ncr.quantity_defective}</td>
              <td>
                <Badge variant={getStatusVariant(ncr.status)} size="sm">
                  {ncr.status}
                </Badge>
              </td>
              <td className="ncrs-table-actions">
                {ncr.status === 'OPEN' && onReview && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onReview(ncr)
                    }}
                  >
                    Review
                  </Button>
                )}
                {ncr.status === 'IN_REVIEW' && onResolve && (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onResolve(ncr)
                    }}
                  >
                    Resolve
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDelete(ncr)
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
