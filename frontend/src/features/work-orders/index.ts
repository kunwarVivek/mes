/**
 * Work Orders Module Entry Point
 *
 * Exports all public APIs for the work-orders feature module
 */

// Types
export type {
  WorkOrder,
  CreateWorkOrderDTO,
  UpdateWorkOrderDTO,
  WorkOrderListResponse,
  WorkOrderFilters,
  OrderType,
  OrderStatus,
  WorkOrderOperation,
  WorkOrderMaterial,
} from './types/workOrder.types'

// Schemas
export {
  createWorkOrderSchema,
  updateWorkOrderSchema,
  orderTypeSchema,
  orderStatusSchema,
} from './schemas/workOrder.schema'
export type {
  CreateWorkOrderFormData,
  UpdateWorkOrderFormData,
} from './schemas/workOrder.schema'

// Services
export { workOrderService } from './services/workOrder.service'

// Hooks
export { useWorkOrders, WORK_ORDERS_QUERY_KEY } from './hooks/useWorkOrders'
export { useWorkOrder } from './hooks/useWorkOrder'
export { useCreateWorkOrder } from './hooks/useCreateWorkOrder'
export { useUpdateWorkOrder } from './hooks/useUpdateWorkOrder'
export { useDeleteWorkOrder } from './hooks/useDeleteWorkOrder'
export { useReleaseWorkOrder } from './hooks/useReleaseWorkOrder'
export { useStartWorkOrder } from './hooks/useStartWorkOrder'
export { useCompleteWorkOrder } from './hooks/useCompleteWorkOrder'
