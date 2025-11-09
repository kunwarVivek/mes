/**
 * Work Order Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

// Enums matching backend DTOs
export const orderTypeSchema = z.enum(['PRODUCTION', 'REWORK', 'ASSEMBLY'])
export const orderStatusSchema = z.enum([
  'PLANNED',
  'RELEASED',
  'IN_PROGRESS',
  'COMPLETED',
  'CANCELLED',
])
export const operationStatusSchema = z.enum(['PENDING', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED'])

// WorkOrderOperation schema
export const workOrderOperationSchema = z.object({
  id: z.number(),
  work_order_id: z.number(),
  operation_sequence: z.number(),
  operation_name: z.string(),
  status: operationStatusSchema,
  setup_time_minutes: z.number().optional(),
  run_time_minutes: z.number().optional(),
  actual_setup_time_minutes: z.number().optional(),
  actual_run_time_minutes: z.number().optional(),
})

// WorkOrderMaterial schema
export const workOrderMaterialSchema = z.object({
  id: z.number(),
  work_order_id: z.number(),
  material_id: z.number(),
  required_quantity: z.number(),
  allocated_quantity: z.number(),
  issued_quantity: z.number().optional(),
})

// CreateWorkOrderRequest schema
export const createWorkOrderSchema = z.object({
  material_id: z.number().gt(0, 'Material ID must be greater than 0'),
  order_type: orderTypeSchema.default('PRODUCTION'),
  planned_quantity: z.number().gt(0, 'Planned quantity must be greater than 0'),
  start_date_planned: z.coerce.date().optional(),
  end_date_planned: z.coerce.date().optional(),
  priority: z.number().min(1, 'Priority must be at least 1').max(10, 'Priority must be at most 10').default(5),
})

// WorkOrderResponse schema
export const workOrderResponseSchema = z.object({
  id: z.number(),
  organization_id: z.number(),
  plant_id: z.number(),
  work_order_number: z.string(),
  material_id: z.number(),
  order_type: z.string(),
  order_status: z.string(),
  planned_quantity: z.number(),
  actual_quantity: z.number(),
  start_date_planned: z.coerce.date().optional(),
  start_date_actual: z.coerce.date().optional(),
  end_date_planned: z.coerce.date().optional(),
  end_date_actual: z.coerce.date().optional(),
  priority: z.number(),
  created_by_user_id: z.number(),
  created_at: z.coerce.date(),
  updated_at: z.coerce.date().optional(),
  operations: z.array(workOrderOperationSchema),
  materials: z.array(workOrderMaterialSchema),
})

// UpdateWorkOrderRequest schema (partial updates)
export const updateWorkOrderSchema = z.object({
  planned_quantity: z.number().gt(0).optional(),
  start_date_planned: z.coerce.date().optional(),
  end_date_planned: z.coerce.date().optional(),
  priority: z.number().min(1).max(10).optional(),
})

// Type exports
export type OrderType = z.infer<typeof orderTypeSchema>
export type OrderStatus = z.infer<typeof orderStatusSchema>
export type OperationStatus = z.infer<typeof operationStatusSchema>
export type WorkOrderOperation = z.infer<typeof workOrderOperationSchema>
export type WorkOrderMaterial = z.infer<typeof workOrderMaterialSchema>
export type CreateWorkOrderFormData = z.infer<typeof createWorkOrderSchema>
export type UpdateWorkOrderFormData = z.infer<typeof updateWorkOrderSchema>
export type WorkOrder = z.infer<typeof workOrderResponseSchema>
