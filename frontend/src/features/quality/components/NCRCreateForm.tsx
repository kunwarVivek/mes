/**
 * NCRCreateForm Component
 *
 * Form for creating new NCRs
 */
import { useState } from 'react'
import { Button } from '@/design-system/atoms/Button'
import { Input } from '@/design-system/atoms/Input'
import { Textarea } from '@/design-system/atoms/Textarea'
import { useAuthStore } from '@/stores/auth.store'
import type { CreateNCRDTO, DefectType } from '../types/ncr.types'

export interface NCRCreateFormProps {
  onSubmit: (data: CreateNCRDTO) => void
  onCancel: () => void
}

export function NCRCreateForm({ onSubmit, onCancel }: NCRCreateFormProps) {
  const { currentOrg, currentPlant, user } = useAuthStore()

  const [formData, setFormData] = useState({
    ncr_number: '',
    defect_type: 'MATERIAL' as DefectType,
    work_order_id: '',
    material_id: '',
    quantity_affected: '',
    description: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!currentOrg || !currentPlant || !user) {
      return
    }

    onSubmit({
      organization_id: currentOrg.id,
      plant_id: currentPlant.id,
      ncr_number: formData.ncr_number,
      defect_type: formData.defect_type,
      work_order_id: formData.work_order_id ? Number(formData.work_order_id) : undefined,
      material_id: formData.material_id ? Number(formData.material_id) : undefined,
      quantity_affected: Number(formData.quantity_affected),
      description: formData.description,
      reported_by: user.id,
    })
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 p-4 border rounded bg-white shadow"
      data-testid="ncr-create-form"
    >
      <h2 className="text-xl font-semibold mb-4">Create Non-Conformance Report</h2>

      <div>
        <label htmlFor="ncr_number" className="block text-sm font-medium mb-1">
          NCR Number
        </label>
        <Input
          id="ncr_number"
          value={formData.ncr_number}
          onChange={(e) => setFormData({ ...formData, ncr_number: e.target.value })}
          required
          placeholder="NCR-2025-001"
          fullWidth
        />
      </div>

      <div>
        <label htmlFor="defect_type" className="block text-sm font-medium mb-1">
          Defect Type
        </label>
        <select
          id="defect_type"
          value={formData.defect_type}
          onChange={(e) => setFormData({ ...formData, defect_type: e.target.value as DefectType })}
          className="w-full px-3 py-2 border rounded"
        >
          <option value="MATERIAL">Material</option>
          <option value="PROCESS">Process</option>
          <option value="EQUIPMENT">Equipment</option>
          <option value="WORKMANSHIP">Workmanship</option>
          <option value="DESIGN">Design</option>
          <option value="OTHER">Other</option>
        </select>
      </div>

      <div>
        <label htmlFor="work_order_id" className="block text-sm font-medium mb-1">
          Work Order ID (Optional)
        </label>
        <Input
          id="work_order_id"
          type="number"
          value={formData.work_order_id}
          onChange={(e) => setFormData({ ...formData, work_order_id: e.target.value })}
          fullWidth
        />
      </div>

      <div>
        <label htmlFor="material_id" className="block text-sm font-medium mb-1">
          Material ID (Optional)
        </label>
        <Input
          id="material_id"
          type="number"
          value={formData.material_id}
          onChange={(e) => setFormData({ ...formData, material_id: e.target.value })}
          fullWidth
        />
      </div>

      <div>
        <label htmlFor="quantity_affected" className="block text-sm font-medium mb-1">
          Quantity Affected
        </label>
        <Input
          id="quantity_affected"
          type="number"
          value={formData.quantity_affected}
          onChange={(e) => setFormData({ ...formData, quantity_affected: e.target.value })}
          required
          fullWidth
        />
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium mb-1">
          Description
        </label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(value) => setFormData({ ...formData, description: value })}
          rows={4}
          placeholder="Describe the non-conformance in detail..."
        />
      </div>

      <div className="flex gap-2">
        <Button type="submit">Create NCR</Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
