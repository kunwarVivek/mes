/**
 * Production Module
 *
 * Production planning and management module exports
 */

// Types
export type {
  ProductionPlan,
  ProductionPlanStatus,
  CreateProductionPlanDTO,
  UpdateProductionPlanDTO,
  ProductionPlanListResponse,
  ProductionPlanFilters,
} from './types/production.types'

// Schemas
export {
  productionPlanStatusSchema,
  createProductionPlanSchema,
  updateProductionPlanSchema,
} from './schemas/production.schema'
export type {
  CreateProductionPlanFormData,
  UpdateProductionPlanFormData,
} from './schemas/production.schema'

// Services
export { productionService } from './services/production.service'

// Hooks
export { useProductionPlans, PRODUCTION_PLANS_QUERY_KEY } from './hooks/useProductionPlans'
export { useProductionPlan } from './hooks/useProductionPlan'
export { useCreateProductionPlan } from './hooks/useCreateProductionPlan'
export { useUpdateProductionPlan } from './hooks/useUpdateProductionPlan'
export { useDeleteProductionPlan } from './hooks/useDeleteProductionPlan'

// Components
export { ProductionPlansTable } from './components/ProductionPlansTable'
export type { ProductionPlansTableProps } from './components/ProductionPlansTable'
export { ProductionPlanForm } from './components/ProductionPlanForm'
export type { ProductionPlanFormProps } from './components/ProductionPlanForm'
export { ProductionEntryForm } from './components/ProductionEntryForm'
export type { ProductionEntryFormProps } from './components/ProductionEntryForm'
export { ProductionSummaryCard } from './components/ProductionSummaryCard'
export type { ProductionSummaryCardProps } from './components/ProductionSummaryCard'
export { ProductionLogsTable } from './components/ProductionLogsTable'
export type { ProductionLogsTableProps } from './components/ProductionLogsTable'

// Pages
export { ProductionDashboardPage } from './pages/ProductionDashboardPage'

// Production Logging Types
export type {
  ProductionLog,
  ProductionLogCreateRequest,
  ProductionLogListResponse,
  ProductionSummary,
  ProductionLogFilters,
} from './types/productionLog.types'

// Production Logging Services
export { productionLogService } from './services/productionLog.service'

// Production Logging Hooks
export {
  useProductionLogs,
  useProductionSummary,
  useProductionLog,
  useLogProduction,
  PRODUCTION_LOGS_QUERY_KEY,
  PRODUCTION_SUMMARY_QUERY_KEY,
  PRODUCTION_LOG_QUERY_KEY,
} from './hooks/useProductionLogs'
