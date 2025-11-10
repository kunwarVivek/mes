import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'

// Import MaintenancePage when it's implemented
// For now, create a placeholder
const MaintenancePage = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold mb-4">Maintenance Management</h1>
    <p>PM schedules, work orders, and downtime tracking</p>
  </div>
)

/**
 * Maintenance Route
 *
 * Handles maintenance management
 * - PM schedules
 * - PM work orders
 * - Downtime events
 * - MTBF/MTTR metrics
 */
export const maintenanceRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/maintenance',
  component: MaintenancePage,
})
