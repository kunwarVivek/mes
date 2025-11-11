import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { BillingPage } from '@/pages/BillingPage'

/**
 * Billing Route
 *
 * Customer-facing billing and subscription management page.
 * Shows current plan, usage, invoices, and upgrade options.
 */

export const billingRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/billing',
  component: BillingPage,
})
