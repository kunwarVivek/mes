/**
 * Scheduling Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const scheduledOperationStatusSchema = z.enum([
  'SCHEDULED',
  'IN_PROGRESS',
  'COMPLETED',
  'CANCELLED',
])

export const createScheduledOperationSchema = z
  .object({
    organization_id: z.number().positive('Organization ID is required'),
    work_order_id: z.number().positive('Work order is required'),
    operation_sequence: z.number().positive('Sequence must be positive'),
    operation_name: z
      .string()
      .min(1, 'Operation name is required')
      .max(200, 'Operation name must be at most 200 characters'),
    machine_id: z.number().positive('Machine ID must be positive').optional(),
    scheduled_start: z.string().min(1, 'Start time is required'),
    scheduled_end: z.string().min(1, 'End time is required'),
    status: scheduledOperationStatusSchema.optional().default('SCHEDULED'),
    priority: z.number().min(1, 'Priority must be at least 1').max(10, 'Priority must be at most 10'),
  })
  .refine((data) => new Date(data.scheduled_end) > new Date(data.scheduled_start), {
    message: 'End time must be after start time',
    path: ['scheduled_end'],
  })

export const updateScheduledOperationSchema = z
  .object({
    operation_name: z
      .string()
      .min(1, 'Operation name is required')
      .max(200, 'Operation name must be at most 200 characters')
      .optional(),
    machine_id: z.number().positive('Machine ID must be positive').optional(),
    scheduled_start: z.string().min(1, 'Start time is required').optional(),
    scheduled_end: z.string().min(1, 'End time is required').optional(),
    actual_start: z.string().optional(),
    actual_end: z.string().optional(),
    status: scheduledOperationStatusSchema.optional(),
    priority: z
      .number()
      .min(1, 'Priority must be at least 1')
      .max(10, 'Priority must be at most 10')
      .optional(),
  })
  .refine(
    (data) => {
      if (data.scheduled_start && data.scheduled_end) {
        return new Date(data.scheduled_end) > new Date(data.scheduled_start)
      }
      return true
    },
    {
      message: 'End time must be after start time',
      path: ['scheduled_end'],
    }
  )
  .refine(
    (data) => {
      if (data.actual_start && data.actual_end) {
        return new Date(data.actual_end) > new Date(data.actual_start)
      }
      return true
    },
    {
      message: 'Actual end time must be after actual start time',
      path: ['actual_end'],
    }
  )

export type CreateScheduledOperationFormData = z.infer<typeof createScheduledOperationSchema>
export type UpdateScheduledOperationFormData = z.infer<typeof updateScheduledOperationSchema>
