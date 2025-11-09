import { createRouter } from '@tanstack/react-router'
import { rootRoute } from './routes/__root'
import { authenticatedRoute } from './routes/_authenticated'
import { indexRoute } from './routes/index'
import { loginRoute } from './routes/login'
import { registerRoute } from './routes/register'
import { materialsRoute } from './routes/materials'
import { usersRoute } from './routes/users'
import { workOrdersRoute } from './routes/work-orders'
import { bomRoute } from './routes/bom'
import { qualityRoute } from './routes/quality'
import { equipmentRoute } from './routes/equipment'

/**
 * TanStack Router Configuration
 *
 * Type-safe routing with code-based route definitions:
 * - Single Responsibility: Router configuration
 * - Type Safety: Full TypeScript support
 * - Route Tree: Hierarchical route structure
 * - Protected Routes: Authentication-based access control
 *
 * Route Structure:
 * - / (root)
 *   - /login (public)
 *   - /register (public)
 *   - /_authenticated (layout + auth guard)
 *     - / (dashboard)
 *     - /materials
 *     - /users
 *     - /work-orders
 *     - /bom
 *     - /quality
 *     - /equipment
 */

// Build route tree with authenticated layout
const routeTree = rootRoute.addChildren([
  loginRoute,
  registerRoute,
  authenticatedRoute.addChildren([
    indexRoute,
    materialsRoute,
    usersRoute,
    workOrdersRoute,
    bomRoute,
    qualityRoute,
    equipmentRoute,
  ]),
])

// Create router instance
export const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
})

// Register router for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
