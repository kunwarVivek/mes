/**
 * WorkOrderTable Component
 *
 * Table for displaying work orders using DataTable organism with StatusBadge and state transitions
 */
import { DataTable, type Column } from '@/design-system/organisms/DataTable'
import { StatusBadge } from '@/design-system/molecules/StatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { WorkOrder, OrderStatus } from '../schemas/work-order.schema'
import { useWorkOrders } from '../hooks/useWorkOrders'
import { useWorkOrderMutations } from '../hooks/useWorkOrderMutations'
import { format } from 'date-fns'

export interface WorkOrderTableProps {
  filters?: {
    status?: string
    material_id?: number
  }
  onRowClick?: (workOrder: WorkOrder) => void
}

// Map OrderStatus to StatusBadge status type
const mapOrderStatusToBadgeStatus = (status: string): any => {
  const statusMap: Record<string, any> = {
    PLANNED: 'planned',
    RELEASED: 'released',
    IN_PROGRESS: 'in_progress',
    COMPLETED: 'completed',
    CANCELLED: 'cancelled',
  }
  return statusMap[status] || 'planned'
}

// Map order type to display label
const orderTypeLabels: Record<string, string> = {
  PRODUCTION: 'Production',
  REWORK: 'Rework',
  ASSEMBLY: 'Assembly',
}

// Map priority number to display
const getPriorityDisplay = (priority: number): string => {
  return priority.toString()
}

export function WorkOrderTable({ filters, onRowClick }: WorkOrderTableProps) {
  const { data, isLoading } = useWorkOrders(filters)
  const { releaseWorkOrder, startWorkOrder, completeWorkOrder } = useWorkOrderMutations()

  const handleRelease = (id: number) => {
    releaseWorkOrder.mutate(id)
  }

  const handleStart = (id: number) => {
    startWorkOrder.mutate(id)
  }

  const handleComplete = (id: number) => {
    completeWorkOrder.mutate(id)
  }

  const renderActions = (workOrder: WorkOrder) => {
    const status = workOrder.order_status

    if (status === 'PLANNED') {
      return (
        <Button
          size="sm"
          variant="outline"
          onClick={(e) => {
            e.stopPropagation()
            handleRelease(workOrder.id)
          }}
        >
          Release
        </Button>
      )
    }

    if (status === 'RELEASED') {
      return (
        <Button
          size="sm"
          variant="outline"
          onClick={(e) => {
            e.stopPropagation()
            handleStart(workOrder.id)
          }}
        >
          Start
        </Button>
      )
    }

    if (status === 'IN_PROGRESS') {
      return (
        <Button
          size="sm"
          variant="outline"
          onClick={(e) => {
            e.stopPropagation()
            handleComplete(workOrder.id)
          }}
        >
          Complete
        </Button>
      )
    }

    // COMPLETED or CANCELLED - no actions
    return null
  }

  const columns: Column<WorkOrder>[] = [
    {
      header: 'WO Number',
      accessor: 'work_order_number',
      sortable: true,
      filterable: true,
      width: '150px',
    },
    {
      header: 'Material',
      accessor: 'material_id',
      sortable: true,
      filterable: true,
      width: '120px',
      render: (value: number) => `MAT-${value}`,
    },
    {
      header: 'Order Type',
      accessor: 'order_type',
      sortable: true,
      filterable: true,
      width: '130px',
      render: (value: string) => (
        <Badge variant="default" className="text-xs">
          {orderTypeLabels[value] || value}
        </Badge>
      ),
    },
    {
      header: 'Status',
      accessor: 'order_status',
      sortable: true,
      width: '150px',
      render: (value: string) => (
        <StatusBadge
          status={mapOrderStatusToBadgeStatus(value)}
          withPulse={value === 'IN_PROGRESS'}
        />
      ),
    },
    {
      header: 'Priority',
      accessor: 'priority',
      sortable: true,
      width: '100px',
      render: (value: number) => getPriorityDisplay(value),
    },
    {
      header: 'Planned Qty',
      accessor: 'planned_quantity',
      sortable: true,
      width: '120px',
    },
    {
      header: 'Planned Dates',
      accessor: (row) => row.start_date_planned,
      width: '200px',
      render: (_value: any, row: WorkOrder) => {
        if (!row.start_date_planned || !row.end_date_planned) {
          return '-'
        }
        return `${format(new Date(row.start_date_planned), 'MMM d')} - ${format(new Date(row.end_date_planned), 'MMM d, yyyy')}`
      },
    },
    {
      header: 'Actions',
      accessor: (row) => row.id,
      width: '120px',
      render: (_value: any, row: WorkOrder) => renderActions(row),
    },
  ]

  const emptyState = (
    <div className="text-center py-8">
      <p className="text-muted-foreground">No work orders found</p>
    </div>
  )

  return (
    <DataTable
      data={data?.items || []}
      columns={columns}
      loading={isLoading}
      onRowClick={onRowClick}
      emptyState={emptyState}
      pagination
      pageSize={25}
      stickyHeader
      rowKey="id"
    />
  )
}
