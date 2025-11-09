/**
 * WorkOrderForm Component
 *
 * Form for creating and editing work orders using React Hook Form + shadcn
 */
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  createWorkOrderSchema,
  updateWorkOrderSchema,
  type CreateWorkOrderFormData,
  type UpdateWorkOrderFormData,
  type WorkOrder,
} from '../schemas/work-order.schema'
import { useWorkOrderMutations } from '../hooks/useWorkOrderMutations'
import { cn } from '@/lib/utils'

export interface WorkOrderFormProps {
  workOrderId?: number
  onSuccess?: () => void
  defaultValues?: Partial<WorkOrder>
}

export function WorkOrderForm({ workOrderId, onSuccess, defaultValues }: WorkOrderFormProps) {
  const isEditMode = !!workOrderId
  const { createWorkOrder, updateWorkOrder } = useWorkOrderMutations()

  const initialFormValues = isEditMode
    ? {
        planned_quantity: defaultValues?.planned_quantity || 0,
        start_date_planned: defaultValues?.start_date_planned,
        end_date_planned: defaultValues?.end_date_planned,
        priority: defaultValues?.priority || 5,
      }
    : {
        material_id: defaultValues?.material_id || 0,
        order_type: (defaultValues?.order_type as any) || 'PRODUCTION',
        planned_quantity: defaultValues?.planned_quantity || 0,
        start_date_planned: defaultValues?.start_date_planned,
        end_date_planned: defaultValues?.end_date_planned,
        priority: defaultValues?.priority || 5,
      }

  const form = useForm<CreateWorkOrderFormData | UpdateWorkOrderFormData>({
    resolver: zodResolver(isEditMode ? updateWorkOrderSchema : createWorkOrderSchema),
    defaultValues: initialFormValues as any,
  })

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
    clearErrors,
  } = form

  // Clear specific field errors when user starts typing
  useEffect(() => {
    const subscription = watch((value, { name }) => {
      if (name && errors[name as keyof typeof errors]) {
        clearErrors(name as keyof typeof errors)
      }
    })
    return () => subscription.unsubscribe()
  }, [watch, errors, clearErrors])

  const onSubmit = async (data: CreateWorkOrderFormData | UpdateWorkOrderFormData) => {
    try {
      if (isEditMode) {
        // Only send changed fields for update
        const changedFields: UpdateWorkOrderFormData = {}
        const currentValues = data as any

        if (currentValues.planned_quantity !== initialFormValues.planned_quantity) {
          changedFields.planned_quantity = currentValues.planned_quantity
        }
        if (currentValues.start_date_planned !== initialFormValues.start_date_planned) {
          changedFields.start_date_planned = currentValues.start_date_planned
        }
        if (currentValues.end_date_planned !== initialFormValues.end_date_planned) {
          changedFields.end_date_planned = currentValues.end_date_planned
        }
        if (currentValues.priority !== initialFormValues.priority) {
          changedFields.priority = currentValues.priority
        }

        await updateWorkOrder.mutateAsync({
          id: workOrderId,
          data: changedFields,
        })
      } else {
        await createWorkOrder.mutateAsync(data as CreateWorkOrderFormData)
      }
      onSuccess?.()
    } catch (error) {
      // Error handled by mutation hooks
    }
  }

  const isPending = createWorkOrder.isPending || updateWorkOrder.isPending || isSubmitting

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Basic Information</h3>

        {/* Material ID */}
        {!isEditMode && (
          <div className="space-y-2">
            <Label htmlFor="material_id">
              Material ID<span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="material_id"
              type="number"
              {...register('material_id' as any, { valueAsNumber: true })}
              disabled={isPending}
              aria-invalid={!!errors.material_id}
              className={cn(errors.material_id && 'border-destructive')}
            />
            {errors.material_id && (
              <p className="text-sm text-destructive">{errors.material_id.message}</p>
            )}
          </div>
        )}

        {/* Material ID (readonly in edit mode) */}
        {isEditMode && (
          <div className="space-y-2">
            <Label htmlFor="material_id">Material ID</Label>
            <Input id="material_id" value={defaultValues?.material_id || ''} disabled readOnly />
          </div>
        )}

        {/* Order Type */}
        {!isEditMode && (
          <div className="space-y-2">
            <Label htmlFor="order_type">
              Order Type<span className="text-destructive ml-1">*</span>
            </Label>
            <Select
              value={watch('order_type' as any) || 'PRODUCTION'}
              onValueChange={(value) => setValue('order_type' as any, value as any)}
              disabled={isPending}
            >
              <SelectTrigger id="order_type">
                <SelectValue placeholder="Select order type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PRODUCTION">Production</SelectItem>
                <SelectItem value="REWORK">Rework</SelectItem>
                <SelectItem value="ASSEMBLY">Assembly</SelectItem>
              </SelectContent>
            </Select>
            {errors.order_type && (
              <p className="text-sm text-destructive">{errors.order_type.message}</p>
            )}
          </div>
        )}

        {/* Planned Quantity */}
        <div className="space-y-2">
          <Label htmlFor="planned_quantity">
            Planned Quantity<span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="planned_quantity"
            type="number"
            step="0.01"
            {...register('planned_quantity', { valueAsNumber: true })}
            disabled={isPending}
            aria-invalid={!!errors.planned_quantity}
            className={cn(errors.planned_quantity && 'border-destructive')}
          />
          {errors.planned_quantity && (
            <p className="text-sm text-destructive">{errors.planned_quantity.message}</p>
          )}
        </div>

        {/* Priority */}
        <div className="space-y-2">
          <Label htmlFor="priority">Priority (1-10)</Label>
          <Input
            id="priority"
            type="number"
            min={1}
            max={10}
            {...register('priority', { valueAsNumber: true })}
            disabled={isPending}
            aria-invalid={!!errors.priority}
            className={cn(errors.priority && 'border-destructive')}
          />
          {errors.priority && <p className="text-sm text-destructive">{errors.priority.message}</p>}
          <p className="text-sm text-muted-foreground">Set priority from 1 (low) to 10 (high)</p>
        </div>
      </div>

      {/* Planning Dates */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Planning Dates</h3>

        <div className="grid grid-cols-2 gap-4">
          {/* Start Date Planned */}
          <div className="space-y-2">
            <Label htmlFor="start_date_planned">Start Date Planned</Label>
            <Input
              id="start_date_planned"
              type="date"
              {...register('start_date_planned')}
              disabled={isPending}
            />
          </div>

          {/* End Date Planned */}
          <div className="space-y-2">
            <Label htmlFor="end_date_planned">End Date Planned</Label>
            <Input
              id="end_date_planned"
              type="date"
              {...register('end_date_planned')}
              disabled={isPending}
            />
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4">
        <Button type="submit" disabled={isPending} className="flex-1">
          {isPending ? 'Submitting...' : isEditMode ? 'Update Work Order' : 'Create Work Order'}
        </Button>
      </div>
    </form>
  )
}
