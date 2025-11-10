import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { LaneSchedulingPage } from '../features/lanes/pages/LaneSchedulingPage'

/**
 * Lanes Route
 *
 * Handles visual lane-based scheduling
 * - Lane management
 * - Work order assignment to lanes
 * - Visual scheduling board
 * - Capacity planning
 */
export const lanesRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/lanes',
  component: LaneSchedulingPage,
})
