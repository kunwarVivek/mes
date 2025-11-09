/**
 * BOM Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const bomTypeSchema = z.enum(['PRODUCTION', 'ENGINEERING', 'PLANNING'])

export const createBOMSchema = z.object({
  bom_number: z
    .string()
    .min(1, 'BOM number is required')
    .max(50, 'BOM number must be at most 50 characters'),
  material_id: z.number().positive('Material is required'),
  bom_name: z
    .string()
    .min(1, 'BOM name is required')
    .max(200, 'BOM name must be at most 200 characters'),
  bom_type: bomTypeSchema,
  base_quantity: z.number().positive('Base quantity must be positive'),
  unit_of_measure_id: z.number().positive('Unit of measure is required'),
  effective_start_date: z.string().optional(),
  effective_end_date: z.string().optional(),
  bom_version: z.number().int().min(1).optional().default(1),
})

export const updateBOMSchema = z.object({
  bom_name: z
    .string()
    .min(1, 'BOM name is required')
    .max(200, 'BOM name must be at most 200 characters')
    .optional(),
  bom_type: bomTypeSchema.optional(),
  base_quantity: z.number().positive('Base quantity must be positive').optional(),
  effective_start_date: z.string().optional(),
  effective_end_date: z.string().optional(),
  is_active: z.boolean().optional(),
})

export type CreateBOMFormData = z.infer<typeof createBOMSchema>
export type UpdateBOMFormData = z.infer<typeof updateBOMSchema>
