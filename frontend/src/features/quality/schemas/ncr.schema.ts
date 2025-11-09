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
    .min(10, 'Description must be at least 10 characters')
    .max(500, 'Description must be at most 500 characters'),
  quantity_defective: z.number().positive('Quantity defective must be positive'),
  reported_by_user_id: z.number().positive('Reporter user ID must be positive'),
  attachment_urls: z.array(z.string().url('Invalid URL')).optional(),
})

export const updateNCRStatusSchema = z.object({
  status: ncrStatusSchema,
  resolution_notes: z
    .string()
    .max(1000, 'Resolution notes must be at most 1000 characters')
    .optional(),
  resolved_by_user_id: z.number().positive('Resolver user ID must be positive').optional(),
}).refine(
  (data) => {
    // Resolution notes required when resolving
    if (data.status === 'RESOLVED' && !data.resolution_notes) {
      return false
    }
    return true
  },
  { message: 'Resolution notes required when resolving NCR', path: ['resolution_notes'] }
)

export type CreateNCRFormData = z.infer<typeof createNCRSchema>
export type UpdateNCRStatusFormData = z.infer<typeof updateNCRStatusSchema>
