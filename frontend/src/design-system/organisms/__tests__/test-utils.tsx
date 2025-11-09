import { ReactNode } from 'react'
import { RouterProvider, createRouter, createRootRoute, createMemoryHistory } from '@tanstack/react-router'
import { render } from '@testing-library/react'

/**
 * Test utility for rendering components with TanStack Router
 */
export function renderWithRouter(
  component: ReactNode,
  { initialPath = '/' }: { initialPath?: string } = {}
) {
  // Create root route
  const rootRoute = createRootRoute({
    component: () => <>{component}</>,
  })

  // Create memory history
  const memoryHistory = createMemoryHistory({
    initialEntries: [initialPath],
  })

  // Create router
  const router = createRouter({
    routeTree: rootRoute,
    history: memoryHistory,
  })

  return render(<RouterProvider router={router} />)
}
