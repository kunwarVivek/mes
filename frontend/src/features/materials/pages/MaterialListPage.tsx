/**
 * MaterialListPage Component
 *
 * List page for materials with search, filter, and navigation
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { SearchBar } from '@/design-system/molecules/SearchBar'
import { FilterGroup } from '@/design-system/molecules/FilterGroup'
import { MaterialTable } from '../components/MaterialTable'
import { useMaterials } from '../hooks/useMaterials'
import type { MaterialListParams } from '../services/material.service'

export function MaterialListPage() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [procurementTypeFilter, setProcurementTypeFilter] = useState<string[]>([])
  const [mrpTypeFilter, setMrpTypeFilter] = useState<string[]>([])

  // Construct query params
  const [queryParams, setQueryParams] = useState<MaterialListParams>({})

  useEffect(() => {
    const params: MaterialListParams = {}

    if (searchQuery) {
      params.search = searchQuery
    }

    if (procurementTypeFilter.length > 0) {
      // Take first selected value (API expects single value)
      params.procurement_type = procurementTypeFilter[0] as any
    }

    if (mrpTypeFilter.length > 0) {
      params.mrp_type = mrpTypeFilter[0] as any
    }

    setQueryParams(params)
  }, [searchQuery, procurementTypeFilter, mrpTypeFilter])

  const { data, isLoading, error } = useMaterials(queryParams)

  const handleRowClick = (material: any) => {
    navigate(`/materials/${material.id}`)
  }

  const handleCreateClick = () => {
    navigate('/materials/create')
  }

  const procurementTypeOptions = [
    { value: 'PURCHASE', label: 'Purchase' },
    { value: 'MANUFACTURE', label: 'Manufacture' },
    { value: 'BOTH', label: 'Both' },
  ]

  const mrpTypeOptions = [
    { value: 'MRP', label: 'MRP' },
    { value: 'REORDER', label: 'Reorder Point' },
  ]

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Materials</h1>
          <p className="text-muted-foreground">Manage your materials and inventory items</p>
        </div>
        <Button onClick={handleCreateClick}>Create Material</Button>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search materials..."
          />
        </div>

        <FilterGroup
          label="Procurement Type"
          options={procurementTypeOptions}
          value={procurementTypeFilter}
          onChange={setProcurementTypeFilter}
        />

        <FilterGroup
          label="MRP Type"
          options={mrpTypeOptions}
          value={mrpTypeFilter}
          onChange={setMrpTypeFilter}
        />
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">
            Failed to load materials. Please try again later.
          </p>
        </div>
      )}

      {/* Materials Table */}
      <MaterialTable
        data={data?.items || []}
        loading={isLoading}
        onRowClick={handleRowClick}
      />
    </div>
  )
}
