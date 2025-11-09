/**
 * MaterialFilters Component
 *
 * Search and filter controls for materials list
 */
import { useState } from 'react'
import { Input, Button } from '@/design-system/atoms'
import type { MaterialFilters as Filters } from '../types/material.types'
import './MaterialFilters.css'

export interface MaterialFiltersProps {
  onFilterChange: (filters: Filters) => void
  isLoading?: boolean
}

export const MaterialFilters = ({ onFilterChange, isLoading }: MaterialFiltersProps) => {
  const [search, setSearch] = useState('')
  const [procurementType, setProcurementType] = useState<string>('')
  const [mrpType, setMrpType] = useState<string>('')
  const [isActive, setIsActive] = useState<string>('')

  const handleApplyFilters = () => {
    const filters: Filters = {}

    if (search.trim()) {
      filters.search = search.trim()
    }

    if (procurementType) {
      filters.procurement_type = procurementType as 'PURCHASE' | 'MANUFACTURE' | 'BOTH'
    }

    if (mrpType) {
      filters.mrp_type = mrpType as 'MRP' | 'REORDER'
    }

    if (isActive !== '') {
      filters.is_active = isActive === 'true'
    }

    onFilterChange(filters)
  }

  const handleClearFilters = () => {
    setSearch('')
    setProcurementType('')
    setMrpType('')
    setIsActive('')
    onFilterChange({})
  }

  return (
    <div className="material-filters">
      <div className="material-filters__search">
        <Input
          type="text"
          placeholder="Search materials..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          disabled={isLoading}
        />
      </div>

      <div className="material-filters__controls">
        <select
          className="material-filters__select"
          value={procurementType}
          onChange={(e) => setProcurementType(e.target.value)}
          disabled={isLoading}
        >
          <option value="">All Procurement Types</option>
          <option value="PURCHASE">Purchase</option>
          <option value="MANUFACTURE">Manufacture</option>
          <option value="BOTH">Both</option>
        </select>

        <select
          className="material-filters__select"
          value={mrpType}
          onChange={(e) => setMrpType(e.target.value)}
          disabled={isLoading}
        >
          <option value="">All MRP Types</option>
          <option value="MRP">MRP</option>
          <option value="REORDER">Reorder Point</option>
        </select>

        <select
          className="material-filters__select"
          value={isActive}
          onChange={(e) => setIsActive(e.target.value)}
          disabled={isLoading}
        >
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>

        <Button variant="primary" onClick={handleApplyFilters} disabled={isLoading}>
          Apply
        </Button>

        <Button variant="ghost" onClick={handleClearFilters} disabled={isLoading}>
          Clear
        </Button>
      </div>
    </div>
  )
}
