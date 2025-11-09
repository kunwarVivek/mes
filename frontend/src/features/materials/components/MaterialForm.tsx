/**
 * MaterialForm Component
 *
 * Form for creating and editing materials using React Hook Form + shadcn
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
  createMaterialSchema,
  updateMaterialSchema,
  type CreateMaterialFormData,
  type UpdateMaterialFormData,
} from '../schemas/material.schema'
import { useMaterialMutations } from '../hooks/useMaterialMutations'
import type { Material } from '../types/material.types'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth.store'

export interface MaterialFormProps {
  materialId?: number
  onSuccess?: () => void
  defaultValues?: Partial<Material>
}

export function MaterialForm({ materialId, onSuccess, defaultValues }: MaterialFormProps) {
  const isEditMode = !!materialId
  const { createMaterial, updateMaterial } = useMaterialMutations()
  const { currentOrg, currentPlant } = useAuthStore()

  const initialFormValues = isEditMode
    ? {
        material_number: defaultValues?.material_number || '',
        material_name: defaultValues?.material_name || '',
        description: defaultValues?.description || '',
        material_category_id: defaultValues?.material_category_id || undefined,
        procurement_type: defaultValues?.procurement_type || 'PURCHASE',
        mrp_type: defaultValues?.mrp_type || 'MRP',
        safety_stock: defaultValues?.safety_stock || 0,
        reorder_point: defaultValues?.reorder_point || 0,
        lot_size: defaultValues?.lot_size || 1,
        lead_time_days: defaultValues?.lead_time_days || 0,
      }
    : {
        organization_id: defaultValues?.organization_id || currentOrg?.id,
        plant_id: defaultValues?.plant_id || currentPlant?.id,
        material_number: '',
        material_name: '',
        description: '',
        material_category_id: undefined,
        base_uom_id: undefined,
        procurement_type: 'PURCHASE',
        mrp_type: 'MRP',
        safety_stock: 0,
        reorder_point: 0,
        lot_size: 1,
        lead_time_days: 0,
      }

  const form = useForm<CreateMaterialFormData | UpdateMaterialFormData>({
    resolver: zodResolver(isEditMode ? updateMaterialSchema : createMaterialSchema),
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

  const onSubmit = async (data: CreateMaterialFormData | UpdateMaterialFormData) => {
    try {
      if (isEditMode) {
        // Only send changed fields for update
        const changedFields: UpdateMaterialFormData = {}
        const currentValues = data as any

        if (currentValues.material_name !== initialFormValues.material_name) {
          changedFields.material_name = currentValues.material_name
        }
        if (currentValues.description !== initialFormValues.description) {
          changedFields.description = currentValues.description
        }
        if (currentValues.material_category_id !== initialFormValues.material_category_id) {
          changedFields.material_category_id = currentValues.material_category_id
        }
        if (currentValues.procurement_type !== initialFormValues.procurement_type) {
          changedFields.procurement_type = currentValues.procurement_type
        }
        if (currentValues.mrp_type !== initialFormValues.mrp_type) {
          changedFields.mrp_type = currentValues.mrp_type
        }
        if (currentValues.safety_stock !== initialFormValues.safety_stock) {
          changedFields.safety_stock = currentValues.safety_stock
        }
        if (currentValues.reorder_point !== initialFormValues.reorder_point) {
          changedFields.reorder_point = currentValues.reorder_point
        }
        if (currentValues.lot_size !== initialFormValues.lot_size) {
          changedFields.lot_size = currentValues.lot_size
        }
        if (currentValues.lead_time_days !== initialFormValues.lead_time_days) {
          changedFields.lead_time_days = currentValues.lead_time_days
        }

        await updateMaterial.mutateAsync({
          id: materialId,
          data: changedFields,
        })
      } else {
        await createMaterial.mutateAsync(data as CreateMaterialFormData)
      }
      onSuccess?.()
    } catch (error) {
      // Error handled by mutation hooks
    }
  }

  const isPending = createMaterial.isPending || updateMaterial.isPending || isSubmitting

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Basic Information</h3>

        {/* Material Number */}
        {!isEditMode && (
          <div className="space-y-2">
            <Label htmlFor="material_number">
              Material Number<span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="material_number"
              {...register('material_number' as any)}
              disabled={isPending}
              aria-invalid={!!errors.material_number}
              className={cn(errors.material_number && 'border-destructive')}
            />
            {errors.material_number && (
              <p className="text-sm text-destructive">{errors.material_number.message}</p>
            )}
            <p className="text-sm text-muted-foreground">
              Uppercase alphanumeric only, max 10 characters
            </p>
          </div>
        )}

        {/* Material Number (readonly in edit mode) */}
        {isEditMode && (
          <div className="space-y-2">
            <Label htmlFor="material_number">Material Number</Label>
            <Input
              id="material_number"
              value={defaultValues?.material_number || ''}
              disabled
              readOnly
            />
          </div>
        )}

        {/* Material Name */}
        <div className="space-y-2">
          <Label htmlFor="material_name">
            Material Name<span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="material_name"
            {...register('material_name')}
            disabled={isPending}
            aria-invalid={!!errors.material_name}
            className={cn(errors.material_name && 'border-destructive')}
          />
          {errors.material_name && (
            <p className="text-sm text-destructive">{errors.material_name.message}</p>
          )}
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <textarea
            id="description"
            {...register('description')}
            disabled={isPending}
            rows={3}
            maxLength={500}
            aria-invalid={!!errors.description}
            className={cn(
              'flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
              errors.description && 'border-destructive'
            )}
          />
          {errors.description && (
            <p className="text-sm text-destructive">{errors.description.message}</p>
          )}
        </div>
      </div>

      {/* Classification */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Classification</h3>

        {/* Material Category */}
        <div className="space-y-2">
          <Label htmlFor="material_category_id">
            Material Category<span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="material_category_id"
            type="number"
            {...register('material_category_id', { valueAsNumber: true })}
            disabled={isPending}
            aria-invalid={!!errors.material_category_id}
            className={cn(errors.material_category_id && 'border-destructive')}
          />
          {errors.material_category_id && (
            <p className="text-sm text-destructive">{errors.material_category_id.message}</p>
          )}
        </div>

        {/* Base UOM (only in create mode) */}
        {!isEditMode && (
          <div className="space-y-2">
            <Label htmlFor="base_uom_id">
              Base UOM<span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="base_uom_id"
              type="number"
              {...register('base_uom_id' as any, { valueAsNumber: true })}
              disabled={isPending}
              aria-invalid={!!errors.base_uom_id}
              className={cn(errors.base_uom_id && 'border-destructive')}
            />
            {errors.base_uom_id && (
              <p className="text-sm text-destructive">{errors.base_uom_id.message}</p>
            )}
          </div>
        )}

        {/* Procurement Type */}
        <div className="space-y-2">
          <Label htmlFor="procurement_type">
            Procurement Type<span className="text-destructive ml-1">*</span>
          </Label>
          <Select
            value={watch('procurement_type') || 'PURCHASE'}
            onValueChange={(value) => setValue('procurement_type', value as any)}
            disabled={isPending}
          >
            <SelectTrigger id="procurement_type">
              <SelectValue placeholder="Select procurement type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="PURCHASE">Purchase</SelectItem>
              <SelectItem value="MANUFACTURE">Manufacture</SelectItem>
              <SelectItem value="BOTH">Both</SelectItem>
            </SelectContent>
          </Select>
          {errors.procurement_type && (
            <p className="text-sm text-destructive">{errors.procurement_type.message}</p>
          )}
        </div>

        {/* MRP Type */}
        <div className="space-y-2">
          <Label htmlFor="mrp_type">
            MRP Type<span className="text-destructive ml-1">*</span>
          </Label>
          <Select
            value={watch('mrp_type') || 'MRP'}
            onValueChange={(value) => setValue('mrp_type', value as any)}
            disabled={isPending}
          >
            <SelectTrigger id="mrp_type">
              <SelectValue placeholder="Select MRP type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="MRP">MRP</SelectItem>
              <SelectItem value="REORDER">Reorder Point</SelectItem>
            </SelectContent>
          </Select>
          {errors.mrp_type && (
            <p className="text-sm text-destructive">{errors.mrp_type.message}</p>
          )}
        </div>
      </div>

      {/* Planning Parameters */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Planning Parameters</h3>

        <div className="grid grid-cols-2 gap-4">
          {/* Safety Stock */}
          <div className="space-y-2">
            <Label htmlFor="safety_stock">Safety Stock</Label>
            <Input
              id="safety_stock"
              type="number"
              {...register('safety_stock', { valueAsNumber: true })}
              disabled={isPending}
              aria-invalid={!!errors.safety_stock}
              className={cn(errors.safety_stock && 'border-destructive')}
            />
            {errors.safety_stock && (
              <p className="text-sm text-destructive">{errors.safety_stock.message}</p>
            )}
          </div>

          {/* Reorder Point */}
          <div className="space-y-2">
            <Label htmlFor="reorder_point">Reorder Point</Label>
            <Input
              id="reorder_point"
              type="number"
              {...register('reorder_point', { valueAsNumber: true })}
              disabled={isPending}
              aria-invalid={!!errors.reorder_point}
              className={cn(errors.reorder_point && 'border-destructive')}
            />
            {errors.reorder_point && (
              <p className="text-sm text-destructive">{errors.reorder_point.message}</p>
            )}
          </div>

          {/* Lot Size */}
          <div className="space-y-2">
            <Label htmlFor="lot_size">Lot Size</Label>
            <Input
              id="lot_size"
              type="number"
              {...register('lot_size', { valueAsNumber: true })}
              disabled={isPending}
              aria-invalid={!!errors.lot_size}
              className={cn(errors.lot_size && 'border-destructive')}
            />
            {errors.lot_size && (
              <p className="text-sm text-destructive">{errors.lot_size.message}</p>
            )}
          </div>

          {/* Lead Time */}
          <div className="space-y-2">
            <Label htmlFor="lead_time_days">Lead Time (Days)</Label>
            <Input
              id="lead_time_days"
              type="number"
              {...register('lead_time_days', { valueAsNumber: true })}
              disabled={isPending}
              aria-invalid={!!errors.lead_time_days}
              className={cn(errors.lead_time_days && 'border-destructive')}
            />
            {errors.lead_time_days && (
              <p className="text-sm text-destructive">{errors.lead_time_days.message}</p>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4">
        <Button type="submit" disabled={isPending} className="flex-1">
          {isPending ? 'Submitting...' : isEditMode ? 'Update Material' : 'Create Material'}
        </Button>
      </div>
    </form>
  )
}
