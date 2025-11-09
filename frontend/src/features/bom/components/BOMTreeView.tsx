/**
 * BOMTreeView Component
 *
 * Hierarchical tree view for Bill of Materials with expand/collapse
 * Supports multi-level nesting and indentation
 */
import { useState } from 'react'
import { Button } from '../../../design-system/atoms/Button'
import type { BOMLineWithChildren } from '../types/bom.types'
import './BOMTreeView.css'

interface BOMTreeViewProps {
  lines: BOMLineWithChildren[]
  onEdit?: (line: BOMLineWithChildren) => void
  onDelete?: (lineId: number) => void
  onAddChild?: (parentLine: BOMLineWithChildren) => void
  level?: number
}

export function BOMTreeView({
  lines,
  onEdit,
  onDelete,
  onAddChild,
  level = 0
}: BOMTreeViewProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set())

  const toggleNode = (lineId: number) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(lineId)) {
      newExpanded.delete(lineId)
    } else {
      newExpanded.add(lineId)
    }
    setExpandedNodes(newExpanded)
  }

  const indent = level * 24 // 24px per level

  if (lines.length === 0) {
    return null
  }

  return (
    <div className="bom-tree">
      {lines.map((line) => {
        const hasChildren = line.children && line.children.length > 0
        const isExpanded = expandedNodes.has(line.id)

        return (
          <div key={line.id} className="bom-tree-item">
            <div
              className="bom-tree-node"
              style={{ paddingLeft: `${indent + 8}px` }}
            >
              {/* Expand/Collapse Toggle */}
              {hasChildren && (
                <button
                  onClick={() => toggleNode(line.id)}
                  className="bom-tree-toggle"
                  aria-label={isExpanded ? 'collapse' : 'expand'}
                >
                  {isExpanded ? '▼' : '▶'}
                </button>
              )}

              {/* Spacer for alignment when no children */}
              {!hasChildren && <div className="bom-tree-spacer" />}

              {/* Line Info */}
              <div className="bom-tree-content">
                <div className="bom-tree-main">
                  <span className="bom-tree-material">
                    {line.component_material_name || `Material #${line.component_material_id}`}
                  </span>
                  <span className="bom-tree-quantity">
                    Qty: {line.quantity} {line.unit_of_measure || 'EA'}
                  </span>
                  <span className="bom-tree-line-number">
                    Line: {line.line_number}
                  </span>
                  {line.scrap_factor > 0 && (
                    <span className="bom-tree-scrap">
                      Scrap: {line.scrap_factor}%
                    </span>
                  )}
                  {line.is_phantom && (
                    <span className="bom-tree-phantom-badge">
                      PHANTOM
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="bom-tree-actions">
                  {onAddChild && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => onAddChild(line)}
                    >
                      Add Child
                    </Button>
                  )}
                  {onEdit && (
                    <Button
                      size="sm"
                      onClick={() => onEdit(line)}
                    >
                      Edit
                    </Button>
                  )}
                  {onDelete && (
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => onDelete(line.id)}
                    >
                      Delete
                    </Button>
                  )}
                </div>
              </div>
            </div>

            {/* Recursive Children */}
            {hasChildren && isExpanded && (
              <BOMTreeView
                lines={line.children!}
                onEdit={onEdit}
                onDelete={onDelete}
                onAddChild={onAddChild}
                level={level + 1}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
