/**
 * Materials Module Exports
 *
 * Central export point for the Materials feature module
 */

// Types
export type * from './types/material.types'

// Schemas
export * from './schemas/material.schema'

// Hooks
export { useMaterials, MATERIALS_QUERY_KEY } from './hooks/useMaterials'
export { useMaterial } from './hooks/useMaterial'
export { useCreateMaterial } from './hooks/useCreateMaterial'
export { useUpdateMaterial } from './hooks/useUpdateMaterial'
export { useDeleteMaterial } from './hooks/useDeleteMaterial'

// Components
export { MaterialsTable } from './components/MaterialsTable'
export { MaterialForm } from './components/MaterialForm'
export { MaterialFilters } from './components/MaterialFilters'

// Pages
export { MaterialsPage } from './pages/MaterialsPage'
export { MaterialFormPage } from './pages/MaterialFormPage'

// Service (for advanced usage)
export { materialService } from './services/material.service'
