import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'

// Import ProductionPlansPage when it's implemented
// For now, create a placeholder
const ProductionPlansPage = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold mb-4">Production Planning</h1>
    <p>Create and manage production plans</p>
  </div>
)

/**
 * Production Plans Route
 *
 * Handles production planning
 * - Create production plans
 * - Approve production plans
 * - Execute plans (generate work orders)
 * - Planning history
 */
export const productionPlansRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/production-plans',
  component: ProductionPlansPage,
})
