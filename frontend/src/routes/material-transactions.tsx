import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './_authenticated'
import MaterialTransactionsPage from '@/pages/MaterialTransactionsPage'

export const materialTransactionsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/material-transactions',
  component: MaterialTransactionsPage,
})
