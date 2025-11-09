import { createRoute } from '@tanstack/react-router'
import { rootRoute } from './__root'
import { LoginPage } from '../features/auth/pages/LoginPage'

/**
 * Login Route (/login)
 *
 * Public authentication route:
 * - Single Responsibility: Login route config
 * - Public: No authentication required
 * - Component: LoginPage
 */

export const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
})
