import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { OrganizationDetailPage } from '@/pages/admin/OrganizationDetailPage'

/**
 * Admin Organization Detail Route
 *
 * View single organization with admin actions.
 * Access: Requires is_superuser=true (checked in component)
 */

export const adminOrganizationDetailRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/admin/organizations/$orgId',
  component: OrganizationDetailPage,
})
