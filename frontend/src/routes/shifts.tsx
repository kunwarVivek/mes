import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'

// Import ShiftsPage when it's implemented
// For now, create a placeholder
const ShiftsPage = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold mb-4">Shift Management</h1>
    <p>Shift patterns, handovers, and performance tracking</p>
  </div>
)

/**
 * Shifts Route
 *
 * Handles shift management
 * - Shift patterns
 * - Shift handovers
 * - Shift performance
 * - Attendance tracking
 */
export const shiftsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/shifts',
  component: ShiftsPage,
})
