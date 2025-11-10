import { createRouter } from '@tanstack/react-router'
import { rootRoute } from './routes/__root'
import { authenticatedRoute } from './routes/_authenticated'
import { indexRoute } from './routes/index'
import { loginRoute } from './routes/login'
import { registerRoute } from './routes/register'
import { materialsRoute, materialsNewRoute } from './routes/materials'
import { usersRoute } from './routes/users'
import { workOrdersRoute, workOrdersNewRoute } from './routes/work-orders'
import { bomRoute } from './routes/bom'
import { qualityRoute, qualityNcrsRoute, qualityNcrsNewRoute } from './routes/quality'
import { equipmentRoute } from './routes/equipment'
// Newly added routes
import { projectsRoute } from './routes/projects'
import { maintenanceRoute } from './routes/maintenance'
import { shiftsRoute } from './routes/shifts'
import { lanesRoute } from './routes/lanes'
import { productionRoute } from './routes/production'
import { productionPlansRoute } from './routes/production-plans'
import { mrpRoute } from './routes/mrp'
import { schedulingRoute } from './routes/scheduling'

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
 *     - /materials (list)
 *     - /materials/new (create)
 *     - /users
 *     - /work-orders (list)
 *     - /work-orders/new (create)
 *     - /bom
 *     - /quality (redirects to /quality/ncrs)
 *     - /quality/ncrs (NCR list)
 *     - /quality/ncrs/new (create NCR)
 *     - /equipment
 *     - /projects (project management)
 *     - /maintenance (PM schedules, work orders)
 *     - /shifts (shift management)
 *     - /lanes (lane-based scheduling)
 *     - /production (production logging)
 *     - /production-plans (production planning)
 *     - /mrp (material requirements planning)
 *     - /scheduling (visual Gantt scheduling)
 */

// Build route tree with authenticated layout
const routeTree = rootRoute.addChildren([
  loginRoute,
  registerRoute,
  authenticatedRoute.addChildren([
    indexRoute,
    materialsRoute,
    materialsNewRoute,
    usersRoute,
    workOrdersRoute,
    workOrdersNewRoute,
    bomRoute,
    qualityRoute,
    qualityNcrsRoute,
    qualityNcrsNewRoute,
    equipmentRoute,
    // Newly added routes
    projectsRoute,
    maintenanceRoute,
    shiftsRoute,
    lanesRoute,
    productionRoute,
    productionPlansRoute,
    mrpRoute,
    schedulingRoute,
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
