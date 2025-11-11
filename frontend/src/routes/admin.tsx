import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { PlatformDashboardPage } from '@/pages/admin/PlatformDashboardPage'

/**
 * Admin Dashboard Route
 *
 * Platform admin dashboard with KPIs and metrics.
 * Access: Requires is_superuser=true (checked in component)
 */

export const adminDashboardRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/admin/dashboard',
  component: PlatformDashboardPage,
})
