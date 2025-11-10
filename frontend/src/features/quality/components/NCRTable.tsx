/**
 * NCRTable Component
 *
 * Table for displaying NCRs using DataTable organism with StatusBadge and dialog
 */
import { useState } from 'react'
import { DataTable, type Column } from '@/design-system/organisms/DataTable'
import { StatusBadge } from '@/design-system/molecules/StatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { NCRStatusUpdateDialog } from './NCRStatusUpdateDialog'
import { useNCRs } from '../hooks/useNCRs'
import { sanitizeHtml } from '@/utils/sanitize'
import type { NCR, NCRStatus } from '../schemas/ncr.schema'
import type { NCRListParams } from '../services/ncr.service'

export interface NCRTableProps {
  filters?: NCRListParams
  onRowClick?: (ncr: NCR) => void
}

export function NCRTable({ filters, onRowClick }: NCRTableProps) {
  const { data, isLoading } = useNCRs(filters)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedNCR, setSelectedNCR] = useState<NCR | null>(null)

  const handleUpdateStatusClick = (ncr: NCR, event: React.MouseEvent) => {
    event.stopPropagation()
    setSelectedNCR(ncr)
    setDialogOpen(true)
  }

  const handleDialogClose = () => {
    setDialogOpen(false)
    setSelectedNCR(null)
  }

  const columns: Column<NCR>[] = [
    {
      header: 'NCR Number',
      accessor: 'ncr_number',
      sortable: true,
      width: '150px',
    },
    {
      header: 'WO ID',
      accessor: 'work_order_id',
      sortable: true,
      width: '100px',
    },
    {
      header: 'Material ID',
      accessor: 'material_id',
      sortable: true,
      width: '120px',
    },
    {
      header: 'Defect Type',
      accessor: 'defect_type',
      width: '150px',
      render: (value: string) => (
        <Badge variant="default" className="text-xs">
          {value}
        </Badge>
      ),
    },
    {
      header: 'Description',
      accessor: 'defect_description',
      render: (value: string) => {
        const sanitized = sanitizeHtml(value)
        const truncated = sanitized.length > 50 ? `${sanitized.substring(0, 50)}...` : sanitized
        return (
          <span
            title={sanitized}
            dangerouslySetInnerHTML={{ __html: truncated }}
          />
        )
      },
    },
    {
      header: 'Qty Defective',
      accessor: 'quantity_defective',
      width: '130px',
      render: (value: number) => value.toFixed(2),
    },
    {
      header: 'Status',
      accessor: 'status',
      width: '130px',
      render: (value: string) => <StatusBadge status={value as NCRStatus} />,
    },
    {
      header: 'Created Date',
      accessor: 'created_at',
      sortable: true,
      width: '150px',
      render: (value: Date) => new Date(value).toLocaleDateString(),
    },
    {
      header: 'Actions',
      accessor: (row: NCR) => row,
      width: '150px',
      render: (_value: NCR, row: NCR) => (
        <Button
          variant="outline"
          size="sm"
          disabled={row.status === 'CLOSED'}
          onClick={(e) => handleUpdateStatusClick(row, e)}
        >
          Update Status
        </Button>
      ),
    },
  ]

  return (
    <>
      <DataTable
        data={data?.items || []}
        columns={columns}
        loading={isLoading}
        onRowClick={onRowClick}
        pagination
        pageSize={25}
        stickyHeader
        rowKey="id"
      />

      {selectedNCR && (
        <NCRStatusUpdateDialog
          ncr={selectedNCR}
          open={dialogOpen}
          onOpenChange={handleDialogClose}
        />
      )}
    </>
  )
}
