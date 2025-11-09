/**
 * BOMsTable Component
 *
 * Table for displaying BOMs with actions (edit, delete)
 */
import { Button, Badge, Skeleton } from '@/design-system/atoms'
import { EmptyState } from '@/design-system/molecules'
import type { BOM } from '../types/bom.types'
import './BOMsTable.css'

export interface BOMsTableProps {
  boms: BOM[]
  isLoading?: boolean
  onEdit?: (bom: BOM) => void
  onDelete?: (bom: BOM) => void
  onRowClick?: (bom: BOM) => void
}

export const BOMsTable = ({
  boms,
  isLoading,
  onEdit,
  onDelete,
  onRowClick,
}: BOMsTableProps) => {
  if (isLoading) {
    return (
      <div className="boms-table-skeleton">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} height="48px" />
        ))}
      </div>
    )
  }

  if (boms.length === 0) {
    return (
      <EmptyState
        title="No BOMs found"
        description="No BOMs match your filters. Try adjusting your search criteria."
      />
    )
  }

  return (
    <div className="boms-table-container">
      <table className="boms-table">
        <thead>
          <tr>
            <th>BOM Number</th>
            <th>BOM Name</th>
            <th>Version</th>
            <th>Material ID</th>
            <th>BOM Type</th>
            <th>Base Quantity</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {boms.map((bom) => (
            <tr
              key={bom.id}
              onClick={() => onRowClick?.(bom)}
              className={onRowClick ? 'boms-table-row-clickable' : ''}
            >
              <td className="boms-table-cell-code">{bom.bom_number}</td>
              <td>{bom.bom_name}</td>
              <td>{bom.bom_version}</td>
              <td>{bom.material_id}</td>
              <td>
                <Badge variant="primary" size="sm">
                  {bom.bom_type}
                </Badge>
              </td>
              <td>{bom.base_quantity}</td>
              <td>
                <Badge variant={bom.is_active ? 'success' : 'danger'} size="sm">
                  {bom.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </td>
              <td className="boms-table-actions">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEdit?.(bom)
                  }}
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete?.(bom)
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
