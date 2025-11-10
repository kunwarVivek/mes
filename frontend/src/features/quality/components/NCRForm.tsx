/**
 * NCRForm Component
 *
 * Form for creating NCRs using React Hook Form + shadcn/ui
 */
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  createNCRSchema,
  type CreateNCRFormData,
  type DefectType,
} from '../schemas/ncr.schema'
import { useNCRMutations } from '../hooks/useNCRMutations'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth.store'

export interface NCRFormProps {
  onSuccess?: () => void
}

const defectTypeOptions: { value: DefectType; label: string }[] = [
  { value: 'DIMENSIONAL', label: 'Dimensional' },
  { value: 'VISUAL', label: 'Visual' },
  { value: 'FUNCTIONAL', label: 'Functional' },
  { value: 'MATERIAL', label: 'Material' },
  { value: 'OTHER', label: 'Other' },
]

export function NCRForm({ onSuccess }: NCRFormProps) {
  const { createNCR } = useNCRMutations()
  const { user } = useAuthStore()

  const form = useForm<CreateNCRFormData>({
    resolver: zodResolver(createNCRSchema),
    defaultValues: {
      ncr_number: '',
      work_order_id: undefined,
      material_id: undefined,
      defect_type: 'DIMENSIONAL',
      defect_description: '',
      quantity_defective: undefined,
      reported_by_user_id: user?.id,
      attachment_urls: [],
    },
  })

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
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

  const onSubmit = async (data: CreateNCRFormData) => {
    try {
      await createNCR.mutateAsync(data)
      onSuccess?.()
    } catch (error) {
      // Error handled by mutation hook
    }
  }

  const isPending = createNCR.isPending || isSubmitting

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {/* NCR Details */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">NCR Details</h3>

        {/* NCR Number */}
        <div className="space-y-2">
          <Label htmlFor="ncr_number">
            NCR Number<span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="ncr_number"
            {...register('ncr_number')}
            disabled={isPending}
            aria-invalid={!!errors.ncr_number}
            className={cn(errors.ncr_number && 'border-destructive')}
            placeholder="NCR-2025-001"
          />
          {errors.ncr_number && (
            <p className="text-sm text-destructive">{errors.ncr_number.message}</p>
          )}
          <p className="text-sm text-muted-foreground">Unique identifier, max 50 characters</p>
        </div>

        {/* Work Order ID */}
        <div className="space-y-2">
          <Label htmlFor="work_order_id">
            Work Order ID<span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="work_order_id"
            type="number"
            {...register('work_order_id', { valueAsNumber: true })}
            disabled={isPending}
            aria-invalid={!!errors.work_order_id}
            className={cn(errors.work_order_id && 'border-destructive')}
          />
          {errors.work_order_id && (
            <p className="text-sm text-destructive">{errors.work_order_id.message}</p>
          )}
        </div>

        {/* Material ID */}
        <div className="space-y-2">
          <Label htmlFor="material_id">
            Material ID<span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="material_id"
            type="number"
            {...register('material_id', { valueAsNumber: true })}
            disabled={isPending}
            aria-invalid={!!errors.material_id}
            className={cn(errors.material_id && 'border-destructive')}
          />
          {errors.material_id && (
            <p className="text-sm text-destructive">{errors.material_id.message}</p>
          )}
        </div>
      </div>

      {/* Defect Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Defect Information</h3>

        {/* Defect Type */}
        <div className="space-y-2">
          <Label htmlFor="defect_type">
            Defect Type<span className="text-destructive ml-1">*</span>
          </Label>
          <Select
            value={watch('defect_type') || 'DIMENSIONAL'}
            onValueChange={(value) => setValue('defect_type', value as DefectType)}
            disabled={isPending}
          >
            <SelectTrigger id="defect_type">
              <SelectValue placeholder="Select defect type" />
            </SelectTrigger>
            <SelectContent>
              {defectTypeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.defect_type && (
            <p className="text-sm text-destructive">{errors.defect_type.message}</p>
          )}
        </div>

        {/* Defect Description */}
        <div className="space-y-2">
          <Label htmlFor="defect_description">
            Defect Description<span className="text-destructive ml-1">*</span>
          </Label>
          <Textarea
            id="defect_description"
            {...register('defect_description')}
            disabled={isPending}
            rows={4}
            maxLength={500}
            aria-invalid={!!errors.defect_description}
            className={cn(errors.defect_description && 'border-destructive')}
            placeholder="Describe the defect in detail..."
          />
          {errors.defect_description && (
            <p className="text-sm text-destructive">{errors.defect_description.message}</p>
          )}
          <p className="text-sm text-muted-foreground">Max 500 characters</p>
        </div>

        {/* Quantity Defective */}
        <div className="space-y-2">
          <Label htmlFor="quantity_defective">
            Quantity Defective<span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="quantity_defective"
            type="number"
            step="0.01"
            {...register('quantity_defective', { valueAsNumber: true })}
            disabled={isPending}
            aria-invalid={!!errors.quantity_defective}
            className={cn(errors.quantity_defective && 'border-destructive')}
          />
          {errors.quantity_defective && (
            <p className="text-sm text-destructive">{errors.quantity_defective.message}</p>
          )}
        </div>
      </div>

      {/* Reporter Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Reporter Information</h3>

        {/* Reported By User ID */}
        <div className="space-y-2">
          <Label htmlFor="reported_by_user_id">
            Reported By User ID<span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="reported_by_user_id"
            type="number"
            {...register('reported_by_user_id', { valueAsNumber: true })}
            disabled={isPending}
            aria-invalid={!!errors.reported_by_user_id}
            className={cn(errors.reported_by_user_id && 'border-destructive')}
          />
          {errors.reported_by_user_id && (
            <p className="text-sm text-destructive">{errors.reported_by_user_id.message}</p>
          )}
          <p className="text-sm text-muted-foreground">User ID of person reporting the NCR</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4">
        <Button type="submit" disabled={isPending} className="flex-1">
          {isPending ? 'Submitting...' : 'Create NCR'}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => reset()}
          disabled={isPending}
          className="flex-1"
        >
          Reset
        </Button>
      </div>
    </form>
  )
}
