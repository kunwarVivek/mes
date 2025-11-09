/**
 * Machine Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const machineStatusSchema = z.enum([
  'AVAILABLE',
  'RUNNING',
  'IDLE',
  'DOWN',
  'SETUP',
  'MAINTENANCE',
])

export const createMachineSchema = z.object({
  organization_id: z.number().positive('Organization ID is required'),
  plant_id: z.number().positive('Plant ID is required'),
  machine_code: z
    .string()
    .min(1, 'Machine code is required')
    .max(20, 'Machine code must be at most 20 characters')
    .regex(/^[A-Z0-9]+$/, 'Machine code must be uppercase alphanumeric only'),
  machine_name: z
    .string()
    .min(1, 'Machine name is required')
    .max(200, 'Machine name must be at most 200 characters'),
  description: z
    .string()
    .max(500, 'Description must be at most 500 characters'),
  work_center_id: z.number().positive('Work center is required'),
  status: machineStatusSchema,
})

export const updateMachineSchema = z.object({
  machine_name: z
    .string()
    .min(1, 'Machine name is required')
    .max(200, 'Machine name must be at most 200 characters')
    .optional(),
  description: z
    .string()
    .max(500, 'Description must be at most 500 characters')
    .optional(),
  work_center_id: z.number().positive('Work center is required').optional(),
  status: machineStatusSchema.optional(),
  is_active: z.boolean().optional(),
})

export const machineStatusUpdateSchema = z.object({
  status: machineStatusSchema,
  notes: z.string().max(500, 'Notes must be at most 500 characters').optional(),
})

export type CreateMachineFormData = z.infer<typeof createMachineSchema>
export type UpdateMachineFormData = z.infer<typeof updateMachineSchema>
export type MachineStatusUpdateFormData = z.infer<typeof machineStatusUpdateSchema>
