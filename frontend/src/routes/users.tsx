import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { UsersPage } from '../pages/UsersPage'

/**
 * Users Route (/users)
 *
 * User management route:
 * - Single Responsibility: Users route config
 * - Protected: Requires authentication
 * - Component: UsersPage
 */

export const usersRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/users',
  component: UsersPage,
})
