/**
 * NCRStatusUpdateDialog Component
 *
 * Dialog for updating NCR status with conditional resolution notes
 */
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  updateNCRStatusSchema,
  type UpdateNCRStatusFormData,
  type NCR,
  type NCRStatus,
} from '../schemas/ncr.schema'
import { useNCRMutations } from '../hooks/useNCRMutations'
import { cn } from '@/lib/utils'

export interface NCRStatusUpdateDialogProps {
  ncr: NCR
  open: boolean
  onOpenChange: (open: boolean) => void
}

// Valid status transitions from each status
const statusTransitions: Record<NCRStatus, NCRStatus[]> = {
  OPEN: ['IN_REVIEW', 'RESOLVED', 'CLOSED'],
  IN_REVIEW: ['RESOLVED', 'CLOSED'],
  RESOLVED: ['CLOSED'],
  CLOSED: [], // No transitions from CLOSED
}

const statusLabels: Record<NCRStatus, string> = {
  OPEN: 'Open',
  IN_REVIEW: 'In Review',
  RESOLVED: 'Resolved',
  CLOSED: 'Closed',
}

export function NCRStatusUpdateDialog({
  ncr,
  open,
  onOpenChange,
}: NCRStatusUpdateDialogProps) {
  const { updateNCRStatus } = useNCRMutations()

  const form = useForm<UpdateNCRStatusFormData>({
    resolver: zodResolver(updateNCRStatusSchema),
    defaultValues: {
      status: ncr.status as NCRStatus,
      resolution_notes: '',
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

  const selectedStatus = watch('status')

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (open) {
      reset({
        status: ncr.status as NCRStatus,
        resolution_notes: '',
      })
    }
  }, [open, ncr.status, reset])

  // Clear errors when user types
  useEffect(() => {
    const subscription = watch((value, { name }) => {
      if (name && errors[name as keyof typeof errors]) {
        clearErrors(name as keyof typeof errors)
      }
    })
    return () => subscription.unsubscribe()
  }, [watch, errors, clearErrors])

  const onSubmit = async (data: UpdateNCRStatusFormData) => {
    try {
      updateNCRStatus.mutate(
        { id: ncr.id, data },
        {
          onSuccess: () => {
            onOpenChange(false)
          },
        }
      )
    } catch (error) {
      // Error handled by mutation hook
    }
  }

  const isPending = updateNCRStatus.isPending || isSubmitting

  // Get valid status options for current NCR status
  const validStatuses = statusTransitions[ncr.status as NCRStatus] || []

  // Show resolution notes field only when RESOLVED is selected
  const showResolutionNotes = selectedStatus === 'RESOLVED'

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Update NCR Status</DialogTitle>
          <DialogDescription>
            Update the status for NCR {ncr.ncr_number}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Status Selection */}
          <div className="space-y-2">
            <Label htmlFor="status">
              Status<span className="text-destructive ml-1">*</span>
            </Label>
            <Select
              value={selectedStatus}
              onValueChange={(value) => setValue('status', value as NCRStatus)}
              disabled={isPending}
            >
              <SelectTrigger id="status">
                <SelectValue placeholder="Select status" />
              </SelectTrigger>
              <SelectContent>
                {validStatuses.map((status) => (
                  <SelectItem key={status} value={status}>
                    {statusLabels[status]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.status && (
              <p className="text-sm text-destructive">{errors.status.message}</p>
            )}
          </div>

          {/* Resolution Notes - Conditional */}
          {showResolutionNotes && (
            <div className="space-y-2">
              <Label htmlFor="resolution_notes">
                Resolution Notes<span className="text-destructive ml-1">*</span>
              </Label>
              <Textarea
                id="resolution_notes"
                {...register('resolution_notes')}
                disabled={isPending}
                rows={4}
                maxLength={1000}
                aria-invalid={!!errors.resolution_notes}
                className={cn(errors.resolution_notes && 'border-destructive')}
                placeholder="Describe how the issue was resolved..."
              />
              {errors.resolution_notes && (
                <p className="text-sm text-destructive">{errors.resolution_notes.message}</p>
              )}
              <p className="text-sm text-muted-foreground">
                Required when status is Resolved
              </p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Updating...' : 'Update Status'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
