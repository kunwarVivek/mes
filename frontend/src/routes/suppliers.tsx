import { createFileRoute } from '@tanstack/react-router'
import SuppliersPage from '@/pages/SuppliersPage'

export const Route = createFileRoute('/_authenticated/suppliers')({
  component: SuppliersPage,
})
