import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { OrganizationsPage } from '@/pages/admin/OrganizationsPage'

/**
 * Admin Organizations List Route
 *
 * List all organizations with search and filters.
 * Access: Requires is_superuser=true (checked in component)
 */

export const adminOrganizationsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/admin/organizations',
  component: OrganizationsPage,
})
