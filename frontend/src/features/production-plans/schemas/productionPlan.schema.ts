/**
 * Production Plan Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const planStatusSchema = z.enum(['DRAFT', 'APPROVED', 'IN_PROGRESS', 'COMPLETED'])

export const createProductionPlanSchema = z.object({
  plan_code: z
    .string()
    .min(1, 'Plan code is required')
    .max(50, 'Plan code must be at most 50 characters'),
  plan_name: z
    .string()
    .min(1, 'Plan name is required')
    .max(200, 'Plan name must be at most 200 characters'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  status: planStatusSchema.optional().default('DRAFT'),
})

export const updateProductionPlanSchema = z.object({
  plan_name: z
    .string()
    .min(1, 'Plan name is required')
    .max(200, 'Plan name must be at most 200 characters')
    .optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  status: planStatusSchema.optional(),
})

export type CreateProductionPlanFormData = z.infer<typeof createProductionPlanSchema>
export type UpdateProductionPlanFormData = z.infer<typeof updateProductionPlanSchema>
