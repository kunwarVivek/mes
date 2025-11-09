import { createRoute } from '@tanstack/react-router'
import { rootRoute } from './__root'
import { RegisterPage } from '../features/auth/pages/RegisterPage'

/**
 * Register Route (/register)
 *
 * Public registration route:
 * - Single Responsibility: Register route config
 * - Public: No authentication required
 * - Component: RegisterPage
 */

export const registerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/register',
  component: RegisterPage,
})
