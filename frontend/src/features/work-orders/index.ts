/**
 * Work Orders Feature Module
 *
 * Exports all public APIs for work orders feature
 */

// Schemas and Types
export * from './schemas/work-order.schema'

// Services
export { workOrderService } from './services/work-order.service'
export type {
  WorkOrderListResponse,
  WorkOrderListParams,
  AddOperationRequest,
  AddMaterialRequest,
} from './services/work-order.service'

// Hooks
export { useWorkOrders, WORK_ORDERS_QUERY_KEY } from './hooks/useWorkOrders'
export { useWorkOrder } from './hooks/useWorkOrder'
export { useWorkOrderMutations } from './hooks/useWorkOrderMutations'

// Components
export { WorkOrderForm } from './components/WorkOrderForm'
export { WorkOrderTable } from './components/WorkOrderTable'

// Pages
export { WorkOrderListPage } from './pages/WorkOrderListPage'
export { WorkOrderFormPage } from './pages/WorkOrderFormPage'
