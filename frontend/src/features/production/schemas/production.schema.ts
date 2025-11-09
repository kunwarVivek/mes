/**
 * Production Plan Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const productionPlanStatusSchema = z.enum(['DRAFT', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'])

export const createProductionPlanSchema = z.object({
  plan_code: z
    .string()
    .min(1, 'Plan code is required')
    .max(20, 'Plan code must be at most 20 characters'),
  plan_name: z
    .string()
    .min(1, 'Plan name is required')
    .max(200, 'Plan name must be at most 200 characters'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  status: productionPlanStatusSchema,
  notes: z
    .string()
    .max(1000, 'Notes must be at most 1000 characters')
    .optional(),
}).refine(
  (data) => new Date(data.end_date) >= new Date(data.start_date),
  { message: 'End date must be after or equal to start date', path: ['end_date'] }
)

export const updateProductionPlanSchema = z.object({
  plan_name: z
    .string()
    .min(1, 'Plan name is required')
    .max(200, 'Plan name must be at most 200 characters')
    .optional(),
  start_date: z.string().min(1, 'Start date is required').optional(),
  end_date: z.string().min(1, 'End date is required').optional(),
  status: productionPlanStatusSchema.optional(),
  notes: z
    .string()
    .max(1000, 'Notes must be at most 1000 characters')
    .optional(),
}).refine(
  (data) => {
    if (data.start_date && data.end_date) {
      return new Date(data.end_date) >= new Date(data.start_date)
    }
    return true
  },
  { message: 'End date must be after or equal to start date', path: ['end_date'] }
)

export type CreateProductionPlanFormData = z.infer<typeof createProductionPlanSchema>
export type UpdateProductionPlanFormData = z.infer<typeof updateProductionPlanSchema>
