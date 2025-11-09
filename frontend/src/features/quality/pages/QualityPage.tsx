/**
 * QualityPage Component
 *
 * Main page for NCR management with CRUD operations and filtering
 */
import { useState } from 'react'
import { Button } from '@/design-system/atoms'
import { NCRTable } from '../components/NCRTable'
import { NCRDetailModal } from '../components/NCRDetailModal'
import { NCRCreateForm } from '../components/NCRCreateForm'
import { useNCRs } from '../hooks/useNCRs'
import { useCreateNCR, useUpdateNCR, useDeleteNCR } from '../hooks/useNCRMutations'
import type { NCR, NCRStatus, DefectType, CreateNCRDTO, UpdateNCRDTO } from '../types/ncr.types'

export function QualityPage() {
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false)
  const [selectedNCR, setSelectedNCR] = useState<NCR | null>(null)
  const [statusFilter, setStatusFilter] = useState<NCRStatus | ''>('')
  const [defectFilter, setDefectFilter] = useState<DefectType | ''>('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useNCRs({
    status: statusFilter || undefined,
    defect_type: defectFilter || undefined,
    page,
    page_size: 20,
  })

  const createMutation = useCreateNCR()
  const updateMutation = useUpdateNCR()
  const deleteMutation = useDeleteNCR()

  const handleCreate = async (formData: CreateNCRDTO) => {
    await createMutation.mutateAsync(formData)
    setIsCreateFormOpen(false)
  }

  const handleUpdate = async (formData: UpdateNCRDTO) => {
    if (selectedNCR) {
      await updateMutation.mutateAsync({ id: selectedNCR.id, data: formData })
      setSelectedNCR(null)
    }
  }

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this NCR?')) {
      await deleteMutation.mutateAsync(id)
    }
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Quality Management - NCRs</h1>
        <Button onClick={() => setIsCreateFormOpen(true)}>Create NCR</Button>
      </div>

      {/* Filters */}
      <div className="mb-4 flex gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as any)}
          className="px-3 py-2 border rounded"
          aria-label="Filter by status"
        >
          <option value="">All Statuses</option>
          <option value="OPEN">Open</option>
          <option value="INVESTIGATING">Investigating</option>
          <option value="CORRECTIVE_ACTION">Corrective Action</option>
          <option value="CLOSED">Closed</option>
          <option value="REJECTED">Rejected</option>
        </select>

        <select
          value={defectFilter}
          onChange={(e) => setDefectFilter(e.target.value as any)}
          className="px-3 py-2 border rounded"
          aria-label="Filter by defect type"
        >
          <option value="">All Defect Types</option>
          <option value="MATERIAL">Material</option>
          <option value="PROCESS">Process</option>
          <option value="EQUIPMENT">Equipment</option>
          <option value="WORKMANSHIP">Workmanship</option>
          <option value="DESIGN">Design</option>
          <option value="OTHER">Other</option>
        </select>
      </div>

      {/* Create Form */}
      {isCreateFormOpen && (
        <div className="mb-6">
          <NCRCreateForm onSubmit={handleCreate} onCancel={() => setIsCreateFormOpen(false)} />
        </div>
      )}

      {/* Table */}
      <NCRTable
        ncrs={data?.items || []}
        onView={setSelectedNCR}
        onDelete={handleDelete}
        isLoading={isLoading}
      />

      {/* Detail Modal */}
      {selectedNCR && (
        <NCRDetailModal
          ncr={selectedNCR}
          onUpdate={handleUpdate}
          onClose={() => setSelectedNCR(null)}
        />
      )}

      {/* Pagination */}
      {data && data.total > 20 && (
        <div className="mt-4 flex justify-center gap-2">
          <Button variant="secondary" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="px-4 py-2">
            Page {page} of {Math.ceil(data.total / 20)}
          </span>
          <Button
            variant="secondary"
            disabled={page >= Math.ceil(data.total / 20)}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
