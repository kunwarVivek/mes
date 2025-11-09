import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { MaterialListPage } from '../features/materials/pages/MaterialListPage'
import { MaterialFormPage } from '../features/materials/pages/MaterialFormPage'

/**
 * Materials Routes
 *
 * Materials management routes:
 * - /materials - Material list view
 * - /materials/new - Create new material
 *
 * Single Responsibility: Materials route configuration
 * Protected: Requires authentication
 */

export const materialsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/materials',
  component: MaterialListPage,
})

export const materialsNewRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/materials/new',
  component: MaterialFormPage,
})
