/**
 * DataTable Usage Example
 *
 * Demonstrates how to use the DataTable organism in a real page.
 * This example shows Materials list page implementation.
 */

import { useState } from 'react'
import { DataTable, Column, Badge, Button } from '@/design-system'

// Data type definition
interface Material {
  id: number
  material_code: string
  name: string
  description: string
  category: 'raw_material' | 'wip' | 'finished_good'
  stock_quantity: number
  unit_of_measure: string
  min_stock_level: number
  max_stock_level: number
  cost_per_unit: number
  supplier: string
  status: 'active' | 'inactive' | 'discontinued'
}

// Mock data for demonstration
const mockMaterials: Material[] = [
  {
    id: 1,
    material_code: 'RM-001',
    name: 'Steel Sheet 304',
    description: 'Stainless steel sheet, 1.5mm thickness',
    category: 'raw_material',
    stock_quantity: 150,
    unit_of_measure: 'kg',
    min_stock_level: 50,
    max_stock_level: 500,
    cost_per_unit: 5.50,
    supplier: 'ABC Steel Co.',
    status: 'active',
  },
  {
    id: 2,
    material_code: 'WIP-042',
    name: 'Chassis Assembly',
    description: 'Partially assembled chassis unit',
    category: 'wip',
    stock_quantity: 25,
    unit_of_measure: 'units',
    min_stock_level: 10,
    max_stock_level: 100,
    cost_per_unit: 125.00,
    supplier: 'Internal',
    status: 'active',
  },
  {
    id: 3,
    material_code: 'FG-789',
    name: 'Model X Complete',
    description: 'Finished product ready for shipment',
    category: 'finished_good',
    stock_quantity: 75,
    unit_of_measure: 'units',
    min_stock_level: 20,
    max_stock_level: 200,
    cost_per_unit: 450.00,
    supplier: 'Internal',
    status: 'active',
  },
  {
    id: 4,
    material_code: 'RM-015',
    name: 'Aluminum Extrusion',
    description: '6061 aluminum, 2x4 inch profile',
    category: 'raw_material',
    stock_quantity: 5,
    unit_of_measure: 'meters',
    min_stock_level: 50,
    max_stock_level: 300,
    cost_per_unit: 12.75,
    supplier: 'XYZ Metals',
    status: 'active',
  },
  {
    id: 5,
    material_code: 'RM-022',
    name: 'Obsolete Component',
    description: 'Legacy part no longer in use',
    category: 'raw_material',
    stock_quantity: 0,
    unit_of_measure: 'units',
    min_stock_level: 0,
    max_stock_level: 0,
    cost_per_unit: 8.50,
    supplier: 'Old Supplier Inc.',
    status: 'discontinued',
  },
]

export function DataTableExample() {
  const [isLoading] = useState(false)

  // Column definitions
  const columns: Column<Material>[] = [
    {
      header: 'Material Code',
      accessor: 'material_code',
      sortable: true,
      filterable: true,
      width: '150px',
    },
    {
      header: 'Name',
      accessor: 'name',
      sortable: true,
      filterable: true,
      width: '200px',
    },
    {
      header: 'Category',
      accessor: 'category',
      sortable: true,
      filterable: true,
      width: '150px',
      render: (value) => {
        const labels = {
          raw_material: 'Raw Material',
          wip: 'WIP',
          finished_good: 'Finished Good',
        }
        return <Badge variant="info">{labels[value as keyof typeof labels]}</Badge>
      },
    },
    {
      header: 'Stock',
      accessor: 'stock_quantity',
      sortable: true,
      width: '120px',
      render: (value, row) => {
        // Color code stock levels
        const isLow = value <= row.min_stock_level
        const isHigh = value >= row.max_stock_level
        const color = isLow ? 'error' : isHigh ? 'warning' : 'success'

        return (
          <span style={{ color: `var(--color-${color})` }}>
            {value} {row.unit_of_measure}
          </span>
        )
      },
    },
    {
      header: 'Cost/Unit',
      accessor: 'cost_per_unit',
      sortable: true,
      width: '120px',
      render: (value) => `$${value.toFixed(2)}`,
    },
    {
      header: 'Supplier',
      accessor: 'supplier',
      sortable: true,
      filterable: true,
      width: '180px',
    },
    {
      header: 'Status',
      accessor: 'status',
      sortable: true,
      width: '120px',
      render: (value) => {
        const variants = {
          active: 'success',
          inactive: 'warning',
          discontinued: 'error',
        }
        return (
          <Badge variant={variants[value as keyof typeof variants]}>
            {value}
          </Badge>
        )
      },
    },
    {
      header: 'Stock Alert',
      accessor: (row) => {
        // Computed column - stock alert indicator
        if (row.stock_quantity <= row.min_stock_level) {
          return 'low'
        }
        if (row.stock_quantity >= row.max_stock_level) {
          return 'high'
        }
        return 'ok'
      },
      sortable: true,
      width: '100px',
      render: (value) => {
        const icons = {
          low: '⚠️',
          high: '📦',
          ok: '✓',
        }
        const colors = {
          low: 'error',
          high: 'warning',
          ok: 'success',
        }
        return (
          <span style={{ color: `var(--color-${colors[value as keyof typeof colors]})` }}>
            {icons[value as keyof typeof icons]} {value === 'ok' ? 'Normal' : value === 'low' ? 'Reorder' : 'Overstocked'}
          </span>
        )
      },
    },
  ]

  // Row click handler
  const handleRowClick = (material: Material) => {
    console.log('Navigate to material detail:', material.id)
    // In real app: navigate(`/materials/${material.id}`)
  }

  // Custom empty state
  const emptyState = (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <h3>No Materials Found</h3>
      <p style={{ color: 'var(--color-neutral-500)', marginBottom: '1.5rem' }}>
        Start by creating your first material to track inventory.
      </p>
      <Button variant="primary" onClick={() => console.log('Create material')}>
        Create Material
      </Button>
    </div>
  )

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Materials Inventory</h1>
        <p style={{ color: 'var(--color-neutral-600)' }}>
          Manage raw materials, work-in-progress, and finished goods
        </p>
      </div>

      <DataTable
        data={mockMaterials}
        columns={columns}
        loading={isLoading}
        pagination={true}
        pageSize={10}
        pageSizeOptions={[5, 10, 25, 50]}
        onRowClick={handleRowClick}
        emptyState={emptyState}
        stickyHeader={true}
        rowKey="id"
      />

      <div style={{ marginTop: '2rem', padding: '1rem', background: 'var(--color-neutral-50)', borderRadius: '0.5rem' }}>
        <h3>Usage Notes:</h3>
        <ul>
          <li>Click column headers to sort</li>
          <li>Use filter inputs to search within columns</li>
          <li>Click rows to view details (check console)</li>
          <li>Stock levels are color-coded: Red (low), Green (normal), Orange (high)</li>
          <li>Select rows using checkboxes for bulk actions</li>
        </ul>
      </div>
    </div>
  )
}
