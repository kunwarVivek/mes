import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { ProductionDashboardPage } from '../features/production/pages/ProductionDashboardPage'

/**
 * Production Route
 *
 * Handles production logging and monitoring
 * - Production logs
 * - Real-time production tracking
 * - Production metrics
 * - Shop floor data collection
 */
export const productionRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/production',
  component: ProductionDashboardPage,
})
