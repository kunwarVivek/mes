import { createRoute, redirect } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import { NCRListPage } from '../features/quality/pages/NCRListPage'
import { NCRFormPage } from '../features/quality/pages/NCRFormPage'

/**
 * Quality Routes
 *
 * Quality management routes:
 * - /quality - Redirects to /quality/ncrs
 * - /quality/ncrs - NCR list view
 * - /quality/ncrs/new - Create new NCR
 *
 * Single Responsibility: Quality route configuration
 * Protected: Requires authentication
 */

export const qualityRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/quality',
  beforeLoad: () => {
    throw redirect({ to: '/quality/ncrs' })
  },
})

export const qualityNcrsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/quality/ncrs',
  component: NCRListPage,
})

export const qualityNcrsNewRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/quality/ncrs/new',
  component: NCRFormPage,
})
