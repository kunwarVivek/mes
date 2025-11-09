/**
 * Quality Module Exports
 *
 * Central export point for the Quality feature module
 */

// Types
export type * from './types/quality.types'

// Schemas
export * from './schemas/ncr.schema'

// Hooks
export { useNCRs, NCRS_QUERY_KEY } from './hooks/useNCRs'
export { useNCR } from './hooks/useNCR'
export { useCreateNCR } from './hooks/useCreateNCR'
export { useUpdateNCR } from './hooks/useUpdateNCR'
export { useDeleteNCR } from './hooks/useDeleteNCR'
export { useReviewNCR } from './hooks/useReviewNCR'
export { useResolveNCR } from './hooks/useResolveNCR'

// Components
export { NCRsTable } from './components/NCRsTable'
export { NCRForm } from './components/NCRForm'

// Service (for advanced usage)
export { qualityService } from './services/quality.service'
