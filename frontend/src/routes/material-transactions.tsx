import { createFileRoute } from '@tanstack/react-router'
import MaterialTransactionsPage from '@/pages/MaterialTransactionsPage'

export const Route = createFileRoute('/_authenticated/material-transactions')({
  component: MaterialTransactionsPage,
})
