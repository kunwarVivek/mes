/**
 * NCRTable Component
 *
 * Table for displaying NCRs with status/defect badges and actions
 */
import { Button, Badge } from '@/design-system/atoms'
import type { NCR } from '../types/ncr.types'

export interface NCRTableProps {
  ncrs: NCR[]
  isLoading?: boolean
  onView: (ncr: NCR) => void
  onDelete: (id: number) => void
}

const getStatusBadgeVariant = (
  status: string
): 'success' | 'warning' | 'error' | 'info' | 'neutral' => {
  switch (status) {
    case 'CLOSED':
      return 'success'
    case 'CORRECTIVE_ACTION':
      return 'info'
    case 'INVESTIGATING':
      return 'warning'
    case 'OPEN':
    case 'REJECTED':
      return 'error'
    default:
      return 'neutral'
  }
}

const getDefectTypeBadgeVariant = (
  defectType: string
): 'error' | 'warning' | 'info' | 'neutral' => {
  switch (defectType) {
    case 'MATERIAL':
    case 'DESIGN':
      return 'error'
    case 'PROCESS':
    case 'EQUIPMENT':
      return 'warning'
    case 'WORKMANSHIP':
    case 'OTHER':
      return 'info'
    default:
      return 'neutral'
  }
}

export function NCRTable({ ncrs, isLoading, onView, onDelete }: NCRTableProps) {
  if (isLoading) {
    return <div className="p-4">Loading NCRs...</div>
  }

  if (ncrs.length === 0) {
    return null
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">
              NCR Number
            </th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Status</th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">
              Defect Type
            </th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">
              Qty Affected
            </th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">
              Description
            </th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Reported</th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {ncrs.map((ncr) => (
            <tr key={ncr.id} className="hover:bg-gray-50">
              <td className="px-4 py-2 text-sm font-medium text-gray-900">
                {ncr.ncr_number}
              </td>
              <td className="px-4 py-2">
                <Badge
                  variant={getStatusBadgeVariant(ncr.status)}
                  size="sm"
                  className={`badge--${getStatusBadgeVariant(ncr.status)}`}
                >
                  {ncr.status.replace('_', ' ')}
                </Badge>
              </td>
              <td className="px-4 py-2">
                <Badge
                  variant={getDefectTypeBadgeVariant(ncr.defect_type)}
                  size="sm"
                  className={`badge--${getDefectTypeBadgeVariant(ncr.defect_type)}`}
                >
                  {ncr.defect_type}
                </Badge>
              </td>
              <td className="px-4 py-2 text-sm text-gray-700">{ncr.quantity_affected}</td>
              <td className="px-4 py-2">
                <div className="max-w-md truncate text-sm text-gray-700" title={ncr.description}>
                  {ncr.description}
                </div>
              </td>
              <td className="px-4 py-2 text-sm text-gray-700">
                {new Date(ncr.reported_at).toLocaleDateString()}
              </td>
              <td className="px-4 py-2">
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => onView(ncr)}>
                    View
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => onDelete(ncr.id)}>
                    Delete
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
