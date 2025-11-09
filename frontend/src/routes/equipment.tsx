import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { EquipmentPage } from '../features/equipment/pages/EquipmentPage'

/**
 * Equipment Route (/equipment)
 *
 * Equipment management route:
 * - Single Responsibility: Equipment route config
 * - Protected: Requires authentication
 * - Component: EquipmentPage
 */

export const equipmentRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/equipment',
  component: EquipmentPage,
})
