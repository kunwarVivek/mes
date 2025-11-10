import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { ProjectsPage } from '../features/projects/pages/ProjectsPage'

/**
 * Projects Route
 *
 * Handles project and order management
 * - Project CRUD operations
 * - BOM management
 * - Document management
 * - Milestone tracking
 */
export const projectsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/projects',
  component: ProjectsPage,
})
