/**
 * Quality Module - NCR Management
 *
 * Public API exports for Non-Conformance Reports
 */

// Schemas
export * from './schemas/ncr.schema'

// Services
export * from './services/ncr.service'

// Hooks
export { useNCRs } from './hooks/useNCRs'
export { useNCR } from './hooks/useNCR'
export { useNCRMutations } from './hooks/useNCRMutations'
