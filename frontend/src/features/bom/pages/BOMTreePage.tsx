/**
 * BOM Tree Page
 *
 * Main page for managing Bill of Materials with hierarchical tree view
 * Supports multi-level BOMs, phantom BOMs, and scrap factors
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '../../../design-system/atoms/Button'
import { BOMTreeView } from '../components/BOMTreeView'
import { BOMLineForm } from '../components/BOMLineForm'
import { bomService, type BOMTree } from '../services/bom.service'
import { useAuthStore } from '../../../stores/auth.store'
import type { BOMLineWithChildren, CreateBOMLineDTO } from '../types/bom.types'
import type { BOM } from '../types/bom.types'
import './BOMTreePage.css'

export function BOMTreePage() {
  const { currentPlant } = useAuthStore()
  const queryClient = useQueryClient()

  const [selectedBOM, setSelectedBOM] = useState<number | null>(null)
  const [isLineFormOpen, setIsLineFormOpen] = useState(false)
  const [editingLine, setEditingLine] = useState<BOMLineWithChildren | null>(null)
  const [parentLine, setParentLine] = useState<BOMLineWithChildren | null>(null)

  // Fetch BOM headers list
  const { data: bomList, isLoading: isLoadingList } = useQuery({
    queryKey: ['boms', currentPlant?.id],
    queryFn: () => bomService.getAll({ plant_id: currentPlant?.id, is_active: true }),
    enabled: !!currentPlant
  })

  // Fetch BOM tree structure
  const { data: bomTree, isLoading: isTreeLoading } = useQuery({
    queryKey: ['bom-tree', selectedBOM],
    queryFn: () => bomService.getTree(selectedBOM!),
    enabled: !!selectedBOM
  })

  // Mutations
  const createLineMutation = useMutation({
    mutationFn: bomService.createLine,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bom-tree', selectedBOM] })
      setIsLineFormOpen(false)
      setEditingLine(null)
      setParentLine(null)
    }
  })

  const updateLineMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreateBOMLineDTO }) =>
      bomService.updateLine(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bom-tree', selectedBOM] })
      setIsLineFormOpen(false)
      setEditingLine(null)
    }
  })

  const deleteLineMutation = useMutation({
    mutationFn: bomService.deleteLine,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bom-tree', selectedBOM] })
    }
  })

  const handleAddLine = () => {
    setEditingLine(null)
    setParentLine(null)
    setIsLineFormOpen(true)
  }

  const handleAddChild = (line: BOMLineWithChildren) => {
    setEditingLine(null)
    setParentLine(line)
    setIsLineFormOpen(true)
  }

  const handleEditLine = (line: BOMLineWithChildren) => {
    setEditingLine(line)
    setParentLine(null)
    setIsLineFormOpen(true)
  }

  const handleDeleteLine = async (lineId: number) => {
    if (window.confirm('Are you sure you want to delete this BOM line?')) {
      await deleteLineMutation.mutateAsync(lineId)
    }
  }

  const handleSubmitLine = async (formData: CreateBOMLineDTO) => {
    if (editingLine) {
      await updateLineMutation.mutateAsync({ id: editingLine.id, data: formData })
    } else {
      await createLineMutation.mutateAsync(formData)
    }
  }

  const handleCancelForm = () => {
    setIsLineFormOpen(false)
    setEditingLine(null)
    setParentLine(null)
  }

  return (
    <div className="bom-tree-page">
      <div className="bom-tree-page-header">
        <h1 className="bom-tree-page-title">Bill of Materials (BOM)</h1>
      </div>

      <div className="bom-tree-page-content">
        {/* BOM Headers List */}
        <div className="bom-tree-page-sidebar">
          <h2 className="bom-tree-sidebar-title">BOMs</h2>

          {isLoadingList && <div className="bom-tree-loading">Loading BOMs...</div>}

          {!isLoadingList && bomList?.items && bomList.items.length === 0 && (
            <div className="bom-tree-empty">No BOMs found</div>
          )}

          <div className="bom-tree-sidebar-list">
            {bomList?.items?.map((bom: BOM) => (
              <button
                key={bom.id}
                onClick={() => setSelectedBOM(bom.id)}
                className={`bom-tree-sidebar-item ${
                  selectedBOM === bom.id ? 'bom-tree-sidebar-item-active' : ''
                }`}
              >
                <div className="bom-tree-sidebar-item-number">{bom.bom_number}</div>
                <div className="bom-tree-sidebar-item-name">{bom.bom_name}</div>
                <div className="bom-tree-sidebar-item-version">v{bom.bom_version}</div>
              </button>
            ))}
          </div>
        </div>

        {/* BOM Tree View */}
        <div className="bom-tree-page-main">
          {!selectedBOM && (
            <div className="bom-tree-placeholder">
              Select a BOM from the list to view its structure
            </div>
          )}

          {selectedBOM && (
            <>
              <div className="bom-tree-main-header">
                <div>
                  <h2 className="bom-tree-main-title">{bomTree?.bom_number}</h2>
                  <p className="bom-tree-main-subtitle">{bomTree?.bom_name}</p>
                </div>
                <Button onClick={handleAddLine}>Add Component</Button>
              </div>

              {/* Line Form */}
              {isLineFormOpen && selectedBOM && (
                <div className="bom-tree-form-container">
                  <BOMLineForm
                    bomHeaderId={selectedBOM}
                    line={editingLine || undefined}
                    parentLine={parentLine || undefined}
                    onSubmit={handleSubmitLine}
                    onCancel={handleCancelForm}
                  />
                </div>
              )}

              {/* Tree */}
              {isTreeLoading && (
                <div className="bom-tree-loading">Loading BOM structure...</div>
              )}

              {!isTreeLoading && bomTree?.lines && bomTree.lines.length === 0 && (
                <div className="bom-tree-empty-state">
                  No components in this BOM. Click "Add Component" to get started.
                </div>
              )}

              {!isTreeLoading && bomTree?.lines && bomTree.lines.length > 0 && (
                <div className="bom-tree-container">
                  <BOMTreeView
                    lines={bomTree.lines}
                    onEdit={handleEditLine}
                    onDelete={handleDeleteLine}
                    onAddChild={handleAddChild}
                  />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
