/**
 * Maintenance Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const triggerTypeSchema = z.enum(['CALENDAR', 'METER'])
export const pmStatusSchema = z.enum(['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'])
export const downtimeCategorySchema = z.enum([
  'BREAKDOWN',
  'PLANNED_MAINTENANCE',
  'CHANGEOVER',
  'NO_OPERATOR',
  'MATERIAL_SHORTAGE',
])

export const createPMScheduleSchema = z
  .object({
    schedule_code: z
      .string()
      .min(1, 'Schedule code is required')
      .max(20, 'Schedule code must be at most 20 characters')
      .regex(/^[A-Z0-9]+$/, 'Schedule code must be uppercase alphanumeric only'),
    schedule_name: z
      .string()
      .min(1, 'Schedule name is required')
      .max(200, 'Schedule name must be at most 200 characters'),
    machine_id: z.number().positive('Machine is required'),
    trigger_type: triggerTypeSchema,
    frequency_days: z.number().positive('Frequency must be positive').optional(),
    meter_threshold: z.number().positive('Meter threshold must be positive').optional(),
    is_active: z.boolean().default(true),
  })
  .refine(
    (data) => {
      if (data.trigger_type === 'CALENDAR') {
        return data.frequency_days !== undefined && data.frequency_days > 0
      }
      return true
    },
    {
      message: 'Frequency days is required for CALENDAR trigger type',
      path: ['frequency_days'],
    }
  )
  .refine(
    (data) => {
      if (data.trigger_type === 'METER') {
        return data.meter_threshold !== undefined && data.meter_threshold > 0
      }
      return true
    },
    {
      message: 'Meter threshold is required for METER trigger type',
      path: ['meter_threshold'],
    }
  )

export const updatePMScheduleSchema = z.object({
  schedule_name: z
    .string()
    .min(1, 'Schedule name is required')
    .max(200, 'Schedule name must be at most 200 characters')
    .optional(),
  frequency_days: z.number().positive('Frequency must be positive').optional(),
  meter_threshold: z.number().positive('Meter threshold must be positive').optional(),
  is_active: z.boolean().optional(),
})

export const createDowntimeEventSchema = z
  .object({
    machine_id: z.number().positive('Machine is required'),
    category: downtimeCategorySchema,
    reason: z.string().min(1, 'Reason is required').max(500, 'Reason must be at most 500 characters'),
    started_at: z.string().min(1, 'Start time is required'),
    ended_at: z.string().optional(),
    notes: z.string().max(1000, 'Notes must be at most 1000 characters').optional(),
  })
  .refine(
    (data) => {
      if (data.ended_at) {
        return new Date(data.ended_at) > new Date(data.started_at)
      }
      return true
    },
    {
      message: 'End time must be after start time',
      path: ['ended_at'],
    }
  )

export const updateDowntimeEventSchema = z
  .object({
    ended_at: z.string().optional(),
    notes: z.string().max(1000, 'Notes must be at most 1000 characters').optional(),
  })

export type CreatePMScheduleFormData = z.infer<typeof createPMScheduleSchema>
export type UpdatePMScheduleFormData = z.infer<typeof updatePMScheduleSchema>
export type CreateDowntimeEventFormData = z.infer<typeof createDowntimeEventSchema>
export type UpdateDowntimeEventFormData = z.infer<typeof updateDowntimeEventSchema>
