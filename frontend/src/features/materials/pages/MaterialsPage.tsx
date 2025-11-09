/**
 * MaterialsPage Component
 *
 * Main page for materials list with filters and actions
 */
import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { AppLayout } from '@/design-system/templates'
import { Button, Heading1 } from '@/design-system/atoms'
import { MaterialsTable } from '../components/MaterialsTable'
import { MaterialFilters } from '../components/MaterialFilters'
import { useMaterials } from '../hooks/useMaterials'
import { useDeleteMaterial } from '../hooks/useDeleteMaterial'
import type { MaterialFilters as Filters, Material } from '../types/material.types'
import './MaterialsPage.css'

export const MaterialsPage = () => {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<Filters>({})

  const { data, isLoading, error } = useMaterials(filters)
  const deleteMutation = useDeleteMaterial()

  const handleFilterChange = (newFilters: Filters) => {
    setFilters(newFilters)
  }

  const handleCreate = () => {
    navigate({ to: '/materials/create' })
  }

  const handleEdit = (material: Material) => {
    navigate({ to: '/materials/$id/edit', params: { id: material.id } })
  }

  const handleDelete = async (material: Material) => {
    if (window.confirm(`Are you sure you want to delete material ${material.material_number}?`)) {
      try {
        await deleteMutation.mutateAsync(material.id)
      } catch (err) {
        console.error('Failed to delete material:', err)
      }
    }
  }

  const handleRowClick = (material: Material) => {
    navigate({ to: '/materials/$id', params: { id: material.id } })
  }

  return (
    <AppLayout>
      <div className="materials-page">
        <div className="materials-page__header">
          <Heading1>Materials</Heading1>
          <Button variant="primary" onClick={handleCreate}>
            Add Material
          </Button>
        </div>

        <MaterialFilters onFilterChange={handleFilterChange} isLoading={isLoading} />

        {error && (
          <div className="materials-page__error" role="alert">
            Error loading materials: {error instanceof Error ? error.message : 'Unknown error'}
          </div>
        )}

        <MaterialsTable
          materials={data?.items ?? []}
          isLoading={isLoading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onRowClick={handleRowClick}
        />

        {data && data.total > 0 && (
          <div className="materials-page__pagination">
            <p className="materials-page__pagination-info">
              Showing {data.items.length} of {data.total} materials (Page {data.page} of{' '}
              {data.total_pages})
            </p>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
