import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { WorkOrdersPage } from '../features/work-orders/pages/WorkOrdersPage'

/**
 * Work Orders Route (/work-orders)
 *
 * Work orders management route:
 * - Single Responsibility: Work orders route config
 * - Protected: Requires authentication
 * - Component: WorkOrdersPage
 */

export const workOrdersRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/work-orders',
  component: WorkOrdersPage,
})
