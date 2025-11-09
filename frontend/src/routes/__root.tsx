import { createRootRoute, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'

/**
 * Root Route Component
 *
 * Top-level route configuration:
 * - Single Responsibility: Root layout
 * - Provides outlet for child routes
 * - Includes dev tools in development
 */

export const rootRoute = createRootRoute({
  component: () => (
    <>
      <Outlet />
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </>
  ),
})
