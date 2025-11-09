import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { WorkOrderListPage } from '../features/work-orders/pages/WorkOrderListPage'
import { WorkOrderFormPage } from '../features/work-orders/pages/WorkOrderFormPage'

/**
 * Work Orders Routes
 *
 * Work orders management routes:
 * - /work-orders - Work order list view
 * - /work-orders/new - Create new work order
 *
 * Single Responsibility: Work orders route configuration
 * Protected: Requires authentication
 */

export const workOrdersRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/work-orders',
  component: WorkOrderListPage,
})

export const workOrdersNewRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/work-orders/new',
  component: WorkOrderFormPage,
})
