/**
 * MaterialTable Component
 *
 * Table for displaying materials using DataTable organism with StatusBadge
 */
import { DataTable, type Column } from '@/design-system/organisms/DataTable'
import { Badge } from '@/components/ui/badge'
import type { Material } from '../types/material.types'
import { ReactNode } from 'react'

export interface MaterialTableProps {
  data: Material[]
  loading?: boolean
  onRowClick?: (material: Material) => void
  emptyState?: ReactNode
}

export function MaterialTable({ data, loading, onRowClick, emptyState }: MaterialTableProps) {
  const columns: Column<Material>[] = [
    {
      header: 'Material Number',
      accessor: 'material_number',
      sortable: true,
      filterable: true,
      width: '150px',
    },
    {
      header: 'Material Name',
      accessor: 'material_name',
      sortable: true,
      filterable: true,
    },
    {
      header: 'Category',
      accessor: 'material_category_id',
      sortable: true,
      filterable: true,
      width: '120px',
    },
    {
      header: 'UOM',
      accessor: 'base_uom_id',
      sortable: true,
      width: '100px',
    },
    {
      header: 'Procurement Type',
      accessor: 'procurement_type',
      sortable: true,
      filterable: true,
      width: '180px',
      render: (value: string) => (
        <Badge variant="default" className="text-xs">
          {value}
        </Badge>
      ),
    },
    {
      header: 'MRP Type',
      accessor: 'mrp_type',
      sortable: true,
      filterable: true,
      width: '130px',
      render: (value: string) => (
        <Badge variant="secondary" className="text-xs">
          {value}
        </Badge>
      ),
    },
    {
      header: 'Status',
      accessor: 'is_active',
      sortable: true,
      width: '120px',
      render: (value: boolean) => (
        <Badge variant={value ? 'default' : 'destructive'} className="text-xs">
          {value ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
  ]

  return (
    <DataTable
      data={data}
      columns={columns}
      loading={loading}
      onRowClick={onRowClick}
      emptyState={emptyState}
      pagination
      pageSize={25}
      stickyHeader
      rowKey="id"
    />
  )
}
