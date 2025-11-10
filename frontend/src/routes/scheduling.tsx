import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'

// Import SchedulingPage when it's implemented
// For now, create a placeholder
const SchedulingPage = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold mb-4">Visual Production Scheduling</h1>
    <p>Gantt chart view, drag-and-drop scheduling, conflict detection</p>
  </div>
)

/**
 * Scheduling Route
 *
 * Handles visual production scheduling
 * - Gantt chart view
 * - Drag-and-drop rescheduling
 * - Lane reassignment
 * - Conflict detection
 * - Auto-schedule optimization
 */
export const schedulingRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/scheduling',
  component: SchedulingPage,
})
