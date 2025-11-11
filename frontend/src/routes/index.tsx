import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { DashboardPage } from '../pages/DashboardPage'

/**
 * Dashboard Route (/dashboard)
 *
 * Dashboard path - protected route:
 * - Single Responsibility: Dashboard route config
 * - Protected: Requires authentication
 * - Component: DashboardPage
 */

export const indexRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/dashboard',
  component: DashboardPage,
})
