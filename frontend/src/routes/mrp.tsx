import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'

// Import MRPPage when it's implemented
// For now, create a placeholder
const MRPPage = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold mb-4">Material Requirements Planning (MRP)</h1>
    <p>MRP runs, planned orders, and material planning</p>
  </div>
)

/**
 * MRP Route
 *
 * Handles Material Requirements Planning
 * - Execute MRP runs
 * - View planned orders
 * - Convert planned orders to work orders
 * - MRP history and logs
 */
export const mrpRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/mrp',
  component: MRPPage,
})
