/**
 * MRP Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const mrpStatusSchema = z.enum(['DRAFT', 'RUNNING', 'COMPLETED', 'FAILED'])

export const createMRPRunSchema = z.object({
  organization_id: z.number().positive('Organization ID is required'),
  run_code: z
    .string()
    .min(1, 'Run code is required')
    .max(50, 'Run code must be at most 50 characters'),
  run_name: z
    .string()
    .min(1, 'Run name is required')
    .max(200, 'Run name must be at most 200 characters'),
  run_date: z.string().min(1, 'Run date is required'),
  planning_horizon_days: z
    .number()
    .positive('Planning horizon must be positive')
    .max(365, 'Planning horizon must be at most 365 days'),
  status: mrpStatusSchema.optional().default('DRAFT'),
  created_by_user_id: z.number().positive('User ID is required'),
})

export const updateMRPRunSchema = z.object({
  run_name: z
    .string()
    .min(1, 'Run name is required')
    .max(200, 'Run name must be at most 200 characters')
    .optional(),
  run_date: z.string().min(1, 'Run date is required').optional(),
  planning_horizon_days: z
    .number()
    .positive('Planning horizon must be positive')
    .max(365, 'Planning horizon must be at most 365 days')
    .optional(),
  status: mrpStatusSchema.optional(),
})

export type CreateMRPRunFormData = z.infer<typeof createMRPRunSchema>
export type UpdateMRPRunFormData = z.infer<typeof updateMRPRunSchema>
