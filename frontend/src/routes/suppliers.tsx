import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import SuppliersPage from '@/pages/SuppliersPage'

export const suppliersRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/suppliers',
  component: SuppliersPage,
})
