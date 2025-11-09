/**
 * BOM Module Entry Point
 *
 * Exports all public APIs for the bom feature module
 */

// Types
export type {
  BOM,
  BOMLine,
  BOMLineWithChildren,
  CreateBOMDTO,
  UpdateBOMDTO,
  CreateBOMLineDTO,
  UpdateBOMLineDTO,
  BOMListResponse,
  BOMFilters,
  BOMType,
} from './types/bom.types'

// Schemas
export {
  createBOMSchema,
  updateBOMSchema,
  bomTypeSchema,
} from './schemas/bom.schema'
export type {
  CreateBOMFormData,
  UpdateBOMFormData,
} from './schemas/bom.schema'

// Services
export { bomService } from './services/bom.service'
export type { BOMTree } from './services/bom.service'

// Hooks
export { useBOMs, BOMS_QUERY_KEY } from './hooks/useBOMs'
export { useBOM } from './hooks/useBOM'
export { useCreateBOM } from './hooks/useCreateBOM'
export { useUpdateBOM } from './hooks/useUpdateBOM'
export { useDeleteBOM } from './hooks/useDeleteBOM'

// Components
export { BOMsTable } from './components/BOMsTable'
export type { BOMsTableProps } from './components/BOMsTable'
export { BOMForm } from './components/BOMForm'
export type { BOMFormProps } from './components/BOMForm'
export { BOMTreeView } from './components/BOMTreeView'
export { BOMLineForm } from './components/BOMLineForm'

// Pages
export { BOMTreePage } from './pages/BOMTreePage'
