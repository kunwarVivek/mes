import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { BOMPage } from '../features/bom/pages/BOMPage'

/**
 * BOM Route (/bom)
 *
 * Bill of Materials route:
 * - Single Responsibility: BOM route config
 * - Protected: Requires authentication
 * - Component: BOMPage
 */

export const bomRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/bom',
  component: BOMPage,
})
