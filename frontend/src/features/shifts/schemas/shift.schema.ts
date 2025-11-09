/**
 * Shift Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

// Time format validation: HH:MM:SS
const timeFormatRegex = /^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$/

export const createShiftSchema = z.object({
  shift_name: z
    .string()
    .min(1, 'Shift name is required')
    .max(100, 'Shift name must be at most 100 characters'),
  shift_code: z
    .string()
    .min(1, 'Shift code is required')
    .max(10, 'Shift code must be at most 10 characters'),
  start_time: z
    .string()
    .regex(timeFormatRegex, 'Invalid time format (HH:MM:SS)'),
  end_time: z
    .string()
    .regex(timeFormatRegex, 'Invalid time format (HH:MM:SS)'),
  production_target: z
    .number()
    .nonnegative('Production target must be non-negative'),
  is_active: z.boolean().optional().default(true),
})

export const updateShiftSchema = z.object({
  shift_name: z
    .string()
    .min(1, 'Shift name is required')
    .max(100, 'Shift name must be at most 100 characters')
    .optional(),
  start_time: z
    .string()
    .regex(timeFormatRegex, 'Invalid time format (HH:MM:SS)')
    .optional(),
  end_time: z
    .string()
    .regex(timeFormatRegex, 'Invalid time format (HH:MM:SS)')
    .optional(),
  production_target: z
    .number()
    .nonnegative('Production target must be non-negative')
    .optional(),
  is_active: z.boolean().optional(),
})

export const createShiftHandoverSchema = z
  .object({
    from_shift_id: z.number().positive('From shift is required'),
    to_shift_id: z.number().positive('To shift is required'),
    handover_date: z.string().min(1, 'Handover date is required'),
    wip_quantity: z.number().nonnegative('WIP quantity must be non-negative'),
    production_summary: z.string().min(1, 'Production summary is required'),
    quality_issues: z.string().optional(),
    machine_status: z.string().optional(),
    material_status: z.string().optional(),
    safety_incidents: z.string().optional(),
  })
  .refine(
    (data) => data.from_shift_id !== data.to_shift_id,
    { message: 'From and To shifts must be different', path: ['to_shift_id'] }
  )

export type CreateShiftFormData = z.infer<typeof createShiftSchema>
export type UpdateShiftFormData = z.infer<typeof updateShiftSchema>
export type CreateShiftHandoverFormData = z.infer<typeof createShiftHandoverSchema>
