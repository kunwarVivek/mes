import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { SchedulingPage } from '@/features/scheduling/pages/SchedulingPage'

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
