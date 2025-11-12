import { createRootRoute, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import { OfflineIndicator } from '@/components/OfflineIndicator'

/**
 * Root Route Component
 *
 * Top-level route configuration:
 * - Single Responsibility: Root layout
 * - Provides outlet for child routes
 * - Includes dev tools in development
 * - Shows offline indicator for PWA offline queue
 */

export const rootRoute = createRootRoute({
  component: () => (
    <>
      <Outlet />
      <OfflineIndicator />
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </>
  ),
})
