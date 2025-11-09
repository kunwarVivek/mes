/**
 * Material Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const procurementTypeSchema = z.enum(['PURCHASE', 'MANUFACTURE', 'BOTH'])
export const mrpTypeSchema = z.enum(['MRP', 'REORDER'])

export const createMaterialSchema = z.object({
  organization_id: z.number().positive('Organization ID is required'),
  plant_id: z.number().positive('Plant ID is required'),
  material_number: z
    .string()
    .min(1, 'Material number is required')
    .max(10, 'Material number must be at most 10 characters')
    .regex(/^[A-Z0-9]+$/, 'Material number must be uppercase alphanumeric only'),
  material_name: z
    .string()
    .min(1, 'Material name is required')
    .max(200, 'Material name must be at most 200 characters'),
  description: z
    .string()
    .max(500, 'Description must be at most 500 characters')
    .optional(),
  material_category_id: z.number().positive('Material category is required'),
  base_uom_id: z.number().positive('Base UOM is required'),
  procurement_type: procurementTypeSchema,
  mrp_type: mrpTypeSchema,
  safety_stock: z.number().nonnegative('Safety stock must be non-negative').optional().default(0),
  reorder_point: z.number().nonnegative('Reorder point must be non-negative').optional().default(0),
  lot_size: z.number().positive('Lot size must be positive').optional().default(1),
  lead_time_days: z.number().nonnegative('Lead time must be non-negative').optional().default(0),
})

export const updateMaterialSchema = z.object({
  material_name: z
    .string()
    .min(1, 'Material name is required')
    .max(200, 'Material name must be at most 200 characters')
    .optional(),
  description: z
    .string()
    .max(500, 'Description must be at most 500 characters')
    .optional(),
  material_category_id: z.number().positive('Material category is required').optional(),
  procurement_type: procurementTypeSchema.optional(),
  mrp_type: mrpTypeSchema.optional(),
  safety_stock: z.number().nonnegative('Safety stock must be non-negative').optional(),
  reorder_point: z.number().nonnegative('Reorder point must be non-negative').optional(),
  lot_size: z.number().positive('Lot size must be positive').optional(),
  lead_time_days: z.number().nonnegative('Lead time must be non-negative').optional(),
  is_active: z.boolean().optional(),
})

export type CreateMaterialFormData = z.infer<typeof createMaterialSchema>
export type UpdateMaterialFormData = z.infer<typeof updateMaterialSchema>
