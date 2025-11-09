/**
 * Work Order Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const orderTypeSchema = z.enum(['PRODUCTION', 'REWORK', 'ASSEMBLY'])
export const orderStatusSchema = z.enum(['PLANNED', 'RELEASED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'])

export const createWorkOrderSchema = z.object({
  material_id: z.number().positive('Material is required'),
  order_type: orderTypeSchema.optional().default('PRODUCTION'),
  planned_quantity: z.number().positive('Planned quantity must be positive'),
  start_date_planned: z.string().optional(),
  end_date_planned: z.string().optional(),
  priority: z.number().int().min(1).max(10).optional().default(5),
})

export const updateWorkOrderSchema = z.object({
  planned_quantity: z.number().positive('Planned quantity must be positive').optional(),
  start_date_planned: z.string().optional(),
  end_date_planned: z.string().optional(),
  priority: z.number().int().min(1).max(10).optional(),
  order_status: orderStatusSchema.optional(),
})

export type CreateWorkOrderFormData = z.infer<typeof createWorkOrderSchema>
export type UpdateWorkOrderFormData = z.infer<typeof updateWorkOrderSchema>
