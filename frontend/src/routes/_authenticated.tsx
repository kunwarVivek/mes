import { createRoute, redirect, Outlet } from '@tanstack/react-router'
import { rootRoute } from './__root'
import { AppLayout } from '../design-system/templates/AppLayout'
import { useAuthStore } from '../stores/auth.store'

/**
 * Authenticated Layout Route
 *
 * Protected route wrapper with authentication check:
 * - Single Responsibility: Auth guard for protected routes
 * - Redirects to /login if not authenticated
 * - Wraps children in AppLayout
 * - beforeLoad: Runs before route loads
 */

export const authenticatedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: '_authenticated',
  beforeLoad: async ({ location }) => {
    const { isAuthenticated } = useAuthStore.getState()

    if (!isAuthenticated) {
      throw redirect({
        to: '/login',
        search: {
          redirect: location.href,
        },
      })
    }
  },
  component: () => (
    <AppLayout>
      <Outlet />
    </AppLayout>
  ),
})
