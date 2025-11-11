import { createRoute } from '@tanstack/react-router'
import { rootRoute } from './__root'
import { PricingPage } from '../pages/PricingPage'

/**
 * Pricing Page Route (/pricing)
 *
 * Public pricing page:
 * - Single Responsibility: Pricing page route config
 * - Public: No authentication required
 * - Component: PricingPage
 * - B2B SaaS 3-tier pricing model
 */

export const pricingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/pricing',
  component: PricingPage,
})
