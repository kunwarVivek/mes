/**
 * WorkOrderListPage Component
 *
 * List page for work orders with search, filter, and navigation
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { SearchBar } from '@/design-system/molecules/SearchBar'
import { FilterGroup } from '@/design-system/molecules/FilterGroup'
import { WorkOrderTable } from '../components/WorkOrderTable'
import { useWorkOrders } from '../hooks/useWorkOrders'
import type { WorkOrderListParams } from '../services/work-order.service'
import type { WorkOrder } from '../schemas/work-order.schema'

export function WorkOrderListPage() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string[]>([])

  // Construct query params
  const [queryParams, setQueryParams] = useState<WorkOrderListParams>({})

  useEffect(() => {
    const params: WorkOrderListParams = {}

    if (searchQuery) {
      params.search = searchQuery
    }

    if (statusFilter.length > 0) {
      // Take first selected value (API expects single value)
      params.status = statusFilter[0]
    }

    setQueryParams(params)
  }, [searchQuery, statusFilter])

  const { data, isLoading, error } = useWorkOrders(queryParams)

  const handleRowClick = (workOrder: WorkOrder) => {
    navigate(`/work-orders/${workOrder.id}`)
  }

  const handleCreateClick = () => {
    navigate('/work-orders/new')
  }

  const statusOptions = [
    { value: 'PLANNED', label: 'Planned' },
    { value: 'RELEASED', label: 'Released' },
    { value: 'IN_PROGRESS', label: 'In Progress' },
    { value: 'COMPLETED', label: 'Completed' },
    { value: 'CANCELLED', label: 'Cancelled' },
  ]

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Work Orders</h1>
          <p className="text-muted-foreground">Manage your production work orders</p>
        </div>
        <Button onClick={handleCreateClick}>Create Work Order</Button>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search work orders..."
          />
        </div>

        <FilterGroup
          label="Status"
          options={statusOptions}
          value={statusFilter}
          onChange={setStatusFilter}
        />
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">
            Failed to load work orders. Please try again later.
          </p>
        </div>
      )}

      {/* Work Orders Table */}
      <WorkOrderTable
        filters={queryParams}
        onRowClick={handleRowClick}
      />
    </div>
  )
}
