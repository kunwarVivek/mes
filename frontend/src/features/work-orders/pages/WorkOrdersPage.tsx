/**
 * WorkOrdersPage Component
 *
 * Work orders list and management:
 * - Single Responsibility: Work order operations
 * - List, create, update, delete work orders
 * - Protected route (requires authentication)
 */
import { useState } from 'react'
import { Button } from '@/design-system/atoms'
import { WorkOrdersTable } from '../components/WorkOrdersTable'
import { WorkOrderForm } from '../components/WorkOrderForm'
import { useWorkOrders } from '../hooks/useWorkOrders'
import { useCreateWorkOrder } from '../hooks/useCreateWorkOrder'
import { useUpdateWorkOrder } from '../hooks/useUpdateWorkOrder'
import { useDeleteWorkOrder } from '../hooks/useDeleteWorkOrder'
import type { WorkOrder, OrderStatus, CreateWorkOrderDTO, UpdateWorkOrderDTO } from '../types/workOrder.types'
import './WorkOrdersPage.css'

export const WorkOrdersPage = () => {
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingWorkOrder, setEditingWorkOrder] = useState<WorkOrder | null>(null)
  const [statusFilter, setStatusFilter] = useState<OrderStatus | ''>('')
  const [page, setPage] = useState(1)
  const pageSize = 50

  // Query filters
  const filters = {
    status: statusFilter || undefined,
    page,
    page_size: pageSize,
  }

  // Hooks
  const { data, isLoading } = useWorkOrders(filters)
  const createMutation = useCreateWorkOrder()
  const updateMutation = useUpdateWorkOrder()
  const deleteMutation = useDeleteWorkOrder()

  // Handlers
  const handleCreate = () => {
    setEditingWorkOrder(null)
    setIsFormOpen(true)
  }

  const handleEdit = (workOrder: WorkOrder) => {
    setEditingWorkOrder(workOrder)
    setIsFormOpen(true)
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this work order?')) {
      await deleteMutation.mutateAsync(id)
    }
  }

  const handleFormSubmit = async (formData: CreateWorkOrderDTO | UpdateWorkOrderDTO) => {
    try {
      if (editingWorkOrder) {
        await updateMutation.mutateAsync({
          id: editingWorkOrder.id,
          ...(formData as UpdateWorkOrderDTO),
        })
      } else {
        await createMutation.mutateAsync(formData as CreateWorkOrderDTO)
      }
      setIsFormOpen(false)
      setEditingWorkOrder(null)
    } catch (error) {
      // Error is handled by the mutation
      console.error('Form submission error:', error)
    }
  }

  const handleCancel = () => {
    setIsFormOpen(false)
    setEditingWorkOrder(null)
  }

  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value as OrderStatus | '')
    setPage(1) // Reset to first page when filter changes
  }

  const handlePreviousPage = () => {
    setPage((prev) => Math.max(1, prev - 1))
  }

  const handleNextPage = () => {
    if (data && page < data.total_pages) {
      setPage((prev) => prev + 1)
    }
  }

  return (
    <div className="work-orders-page">
      <div className="work-orders-page__header">
        <h1>Work Orders</h1>
        <Button onClick={handleCreate}>Create Work Order</Button>
      </div>

      {/* Filters */}
      <div className="work-orders-page__filters">
        <label htmlFor="status-filter">
          Status:
          <select
            id="status-filter"
            value={statusFilter}
            onChange={handleStatusFilterChange}
            className="work-orders-page__filter-select"
          >
            <option value="">All Statuses</option>
            <option value="PLANNED">Planned</option>
            <option value="RELEASED">Released</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </label>
      </div>

      {/* Form */}
      {isFormOpen && (
        <div className="work-orders-page__form">
          <WorkOrderForm
            mode={editingWorkOrder ? 'edit' : 'create'}
            initialData={editingWorkOrder || undefined}
            onSubmit={handleFormSubmit}
            onCancel={handleCancel}
            isLoading={createMutation.isPending || updateMutation.isPending}
            error={
              createMutation.error?.message || updateMutation.error?.message
            }
          />
        </div>
      )}

      {/* Table */}
      <div className="work-orders-page__table">
        <WorkOrdersTable
          workOrders={data?.items || []}
          isLoading={isLoading}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="work-orders-page__pagination">
          <Button
            onClick={handlePreviousPage}
            disabled={page === 1}
            variant="secondary"
          >
            Previous
          </Button>
          <span className="work-orders-page__pagination-info">
            Page {page} of {data.total_pages}
          </span>
          <Button
            onClick={handleNextPage}
            disabled={page >= data.total_pages}
            variant="secondary"
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}

WorkOrdersPage.displayName = 'WorkOrdersPage'
