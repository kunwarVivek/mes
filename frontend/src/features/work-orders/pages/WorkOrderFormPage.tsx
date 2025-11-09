/**
 * WorkOrderFormPage Component
 *
 * Form page for creating and editing work orders
 */
import { useNavigate, useParams, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/design-system/atoms/Skeleton'
import { WorkOrderForm } from '../components/WorkOrderForm'
import { useWorkOrder } from '../hooks/useWorkOrder'
import { ArrowLeft, ChevronRight } from 'lucide-react'

export function WorkOrderFormPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const workOrderId = id ? parseInt(id, 10) : undefined
  const isEditMode = !!workOrderId

  const { data: workOrder, isLoading, error } = useWorkOrder(workOrderId || 0)

  const handleBack = () => {
    navigate('/work-orders')
  }

  const handleSuccess = () => {
    navigate('/work-orders')
  }

  // Simple breadcrumb component
  const Breadcrumb = () => (
    <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm">
      <Link to="/" className="text-muted-foreground hover:text-foreground">
        Home
      </Link>
      <ChevronRight className="h-4 w-4 text-muted-foreground" />
      <Link to="/work-orders" className="text-muted-foreground hover:text-foreground">
        Work Orders
      </Link>
      <ChevronRight className="h-4 w-4 text-muted-foreground" />
      <span className="font-medium">{isEditMode ? 'Edit' : 'Create'}</span>
    </nav>
  )

  // Loading state for edit mode
  if (isEditMode && isLoading) {
    return (
      <div className="space-y-6 p-6">
        <Breadcrumb />
        <div className="space-y-4">
          <Skeleton variant="text" width="300px" height="40px" />
          <Skeleton variant="rectangular" width="100%" height="400px" />
        </div>
      </div>
    )
  }

  // Error state for edit mode
  if (isEditMode && error) {
    return (
      <div className="space-y-6 p-6">
        <Breadcrumb />
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">
            Failed to load work order. Please try again later.
          </p>
        </div>
        <Button onClick={handleBack} variant="outline">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Work Orders
        </Button>
      </div>
    )
  }

  const pageTitle = isEditMode && workOrder
    ? `Edit Work Order #${workOrder.work_order_number}`
    : 'Create Work Order'

  return (
    <div className="space-y-6 p-6">
      {/* Breadcrumb */}
      <Breadcrumb />

      {/* Header */}
      <div className="flex items-center gap-4">
        <Button onClick={handleBack} variant="ghost" size="icon">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">{pageTitle}</h1>
      </div>

      {/* Form */}
      <div className="max-w-4xl">
        <WorkOrderForm
          workOrderId={workOrderId}
          defaultValues={workOrder}
          onSuccess={handleSuccess}
        />
      </div>
    </div>
  )
}
