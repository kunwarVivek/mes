/**
 * NCR Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const ncrStatusSchema = z.enum(['OPEN', 'IN_REVIEW', 'RESOLVED', 'CLOSED'])
export const defectTypeSchema = z.enum(['DIMENSIONAL', 'VISUAL', 'FUNCTIONAL', 'MATERIAL', 'OTHER'])

export const createNCRSchema = z.object({
  ncr_number: z
    .string()
    .min(1, 'NCR number is required')
    .max(50, 'NCR number must be at most 50 characters'),
  work_order_id: z.number().positive('Work order ID must be positive'),
  material_id: z.number().positive('Material ID must be positive'),
  defect_type: defectTypeSchema,
  defect_description: z
    .string()
    .min(1, 'Defect description is required')
    .max(500, 'Defect description must be at most 500 characters'),
  quantity_defective: z.number().positive('Quantity defective must be positive'),
  reported_by_user_id: z.number().positive('Reporter user ID must be positive'),
  attachment_urls: z.array(z.string()).optional(),
})

export const updateNCRStatusSchema = z
  .object({
    status: ncrStatusSchema,
    resolution_notes: z.string().optional(),
    resolved_by_user_id: z.number().optional(),
  })
  .refine(
    data => {
      // If status is RESOLVED, resolution_notes must be provided and non-empty
      if (data.status === 'RESOLVED') {
        return data.resolution_notes && data.resolution_notes.trim().length > 0
      }
      return true
    },
    {
      message: 'Resolution notes are required when status is RESOLVED',
      path: ['resolution_notes'],
    }
  )

// NCRResponse schema
export const ncrResponseSchema = z.object({
  id: z.number(),
  organization_id: z.number(),
  plant_id: z.number(),
  ncr_number: z.string(),
  work_order_id: z.number(),
  material_id: z.number(),
  defect_type: z.string(),
  defect_description: z.string(),
  quantity_defective: z.number(),
  status: z.string(),
  reported_by_user_id: z.number(),
  attachment_urls: z.array(z.string()).optional(),
  resolution_notes: z.string().optional(),
  resolved_by_user_id: z.number().optional(),
  resolved_at: z.coerce.date().optional(),
  created_at: z.coerce.date(),
  updated_at: z.coerce.date().optional(),
})

// Type exports
export type NCRStatus = z.infer<typeof ncrStatusSchema>
export type DefectType = z.infer<typeof defectTypeSchema>
export type CreateNCRFormData = z.infer<typeof createNCRSchema>
export type UpdateNCRStatusFormData = z.infer<typeof updateNCRStatusSchema>
export type NCR = z.infer<typeof ncrResponseSchema>
