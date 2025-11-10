import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { BOMTreePage } from '../features/bom/pages/BOMTreePage'

/**
 * BOM Route (/bom)
 *
 * Bill of Materials route:
 * - Single Responsibility: BOM route config
 * - Protected: Requires authentication
 * - Component: BOMTreePage (hierarchical tree view with multi-level BOM management)
 */

export const bomRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/bom',
  component: BOMTreePage,
})
