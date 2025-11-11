import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { AnalyticsDashboardPage } from '@/pages/admin/AnalyticsDashboardPage'

/**
 * Admin Analytics Dashboard Route
 *
 * Business intelligence dashboard with revenue metrics.
 * Access: Requires is_superuser=true (checked in component)
 */

export const adminAnalyticsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/admin/analytics',
  component: AnalyticsDashboardPage,
})
