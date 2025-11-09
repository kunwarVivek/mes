import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { QualityPage } from '../features/quality/pages/QualityPage'

/**
 * Quality Route (/quality)
 *
 * Quality control route:
 * - Single Responsibility: Quality route config
 * - Protected: Requires authentication
 * - Component: QualityPage
 */

export const qualityRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/quality',
  component: QualityPage,
})
