/**
 * MaterialsTable Component
 *
 * Table for displaying materials with actions (edit, delete)
 */
import { Button, Badge, Skeleton } from '@/design-system/atoms'
import { EmptyState } from '@/design-system/molecules'
import type { Material } from '../types/material.types'
import './MaterialsTable.css'

export interface MaterialsTableProps {
  materials: Material[]
  isLoading?: boolean
  onEdit?: (material: Material) => void
  onDelete?: (material: Material) => void
  onRowClick?: (material: Material) => void
}

export const MaterialsTable = ({
  materials,
  isLoading,
  onEdit,
  onDelete,
  onRowClick,
}: MaterialsTableProps) => {
  if (isLoading) {
    return (
      <div className="materials-table-skeleton">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} height="48px" />
        ))}
      </div>
    )
  }

  if (materials.length === 0) {
    return (
      <EmptyState
        title="No materials found"
        description="No materials match your filters. Try adjusting your search criteria."
      />
    )
  }

  return (
    <div className="materials-table-container">
      <table className="materials-table">
        <thead>
          <tr>
            <th>Material Number</th>
            <th>Material Name</th>
            <th>Category ID</th>
            <th>UOM ID</th>
            <th>Procurement Type</th>
            <th>MRP Type</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {materials.map((material) => (
            <tr
              key={material.id}
              onClick={() => onRowClick?.(material)}
              className={onRowClick ? 'materials-table-row-clickable' : ''}
            >
              <td className="materials-table-cell-code">{material.material_number}</td>
              <td>{material.material_name}</td>
              <td>{material.material_category_id}</td>
              <td>{material.base_uom_id}</td>
              <td>
                <Badge variant="primary" size="sm">
                  {material.procurement_type}
                </Badge>
              </td>
              <td>
                <Badge variant="secondary" size="sm">
                  {material.mrp_type}
                </Badge>
              </td>
              <td>
                <Badge variant={material.is_active ? 'success' : 'danger'} size="sm">
                  {material.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </td>
              <td className="materials-table-actions">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEdit?.(material)
                  }}
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete?.(material)
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
