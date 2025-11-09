/**
 * NCRDetailModal Component
 *
 * Modal for viewing and updating NCR details
 */
import { useState } from 'react'
import { Button } from '@/design-system/atoms/Button'
import { Textarea } from '@/design-system/atoms/Textarea'
import { Badge } from '@/design-system/atoms/Badge'
import type { NCR, UpdateNCRDTO } from '../types/ncr.types'

export interface NCRDetailModalProps {
  ncr: NCR
  onUpdate: (data: UpdateNCRDTO) => void
  onClose: () => void
}

export function NCRDetailModal({ ncr, onUpdate, onClose }: NCRDetailModalProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    status: ncr.status,
    root_cause: ncr.root_cause || '',
    corrective_action: ncr.corrective_action || '',
    preventive_action: ncr.preventive_action || '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onUpdate(formData)
    setIsEditing(false)
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'CLOSED':
        return 'success'
      case 'CORRECTIVE_ACTION':
        return 'info'
      case 'INVESTIGATING':
        return 'warning'
      default:
        return 'error'
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      data-testid="ncr-detail-modal"
    >
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold">{ncr.ncr_number}</h2>
              <div className="flex gap-2 mt-2">
                <Badge variant={getStatusVariant(ncr.status)}>
                  {ncr.status.replace('_', ' ')}
                </Badge>
                <Badge variant="info">{ncr.defect_type}</Badge>
              </div>
            </div>
            <Button variant="secondary" onClick={onClose}>
              Close
            </Button>
          </div>

          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Quantity Affected
              </label>
              <p className="mt-1 text-lg">{ncr.quantity_affected}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Reported At</label>
              <p className="mt-1">{new Date(ncr.reported_at).toLocaleString()}</p>
            </div>
          </div>

          {/* Description */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <div className="p-3 bg-gray-50 rounded border">{ncr.description}</div>
          </div>

          {/* Edit Form or Read-only */}
          {!isEditing ? (
            <>
              {ncr.root_cause && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Root Cause
                  </label>
                  <div className="p-3 bg-gray-50 rounded border">{ncr.root_cause}</div>
                </div>
              )}

              {ncr.corrective_action && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Corrective Action
                  </label>
                  <div className="p-3 bg-gray-50 rounded border">{ncr.corrective_action}</div>
                </div>
              )}

              {ncr.preventive_action && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preventive Action
                  </label>
                  <div className="p-3 bg-gray-50 rounded border">{ncr.preventive_action}</div>
                </div>
              )}

              <div className="mt-6">
                <Button onClick={() => setIsEditing(true)}>Update NCR</Button>
              </div>
            </>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="OPEN">Open</option>
                  <option value="INVESTIGATING">Investigating</option>
                  <option value="CORRECTIVE_ACTION">Corrective Action</option>
                  <option value="CLOSED">Closed</option>
                  <option value="REJECTED">Rejected</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Root Cause</label>
                <Textarea
                  value={formData.root_cause}
                  onChange={(value) => setFormData({ ...formData, root_cause: value })}
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Corrective Action</label>
                <Textarea
                  value={formData.corrective_action}
                  onChange={(value) => setFormData({ ...formData, corrective_action: value })}
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Preventive Action</label>
                <Textarea
                  value={formData.preventive_action}
                  onChange={(value) => setFormData({ ...formData, preventive_action: value })}
                  rows={3}
                />
              </div>

              <div className="flex gap-2">
                <Button type="submit">Save Changes</Button>
                <Button type="button" variant="secondary" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
