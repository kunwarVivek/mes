import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { MaterialsPage } from '../features/materials/pages/MaterialsPage'

/**
 * Materials Route (/materials)
 *
 * Materials management route:
 * - Single Responsibility: Materials route config
 * - Protected: Requires authentication
 * - Component: MaterialsPage
 */

export const materialsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/materials',
  component: MaterialsPage,
})
