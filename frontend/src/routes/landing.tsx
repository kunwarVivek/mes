import { createRoute, redirect } from '@tanstack/react-router'
import { rootRoute } from './__root'
import { LandingPage } from '../pages/LandingPage'
import { useAuthStore } from '../stores/auth.store'

/**
 * Landing Page Route (/)
 *
 * Public marketing landing page:
 * - Single Responsibility: Landing page route config
 * - Public: No authentication required
 * - Redirects to /dashboard if user is already authenticated
 * - Component: LandingPage
 */

export const landingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: async () => {
    const { isAuthenticated } = useAuthStore.getState()

    // If user is authenticated, redirect to dashboard
    if (isAuthenticated) {
      throw redirect({
        to: '/dashboard',
      })
    }
  },
  component: LandingPage,
})
