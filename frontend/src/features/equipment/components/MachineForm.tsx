/**
 * MachineForm Component
 *
 * Form component for creating and editing machines
 */
import { useState, FormEvent } from 'react'
import { createMachineSchema, updateMachineSchema } from '../schemas/machine.schema'
import type { CreateMachineDTO, UpdateMachineDTO, Machine } from '../types/machine.types'
import { ZodError } from 'zod'
import './MachineForm.css'
import { useAuthStore } from '@/stores/auth.store'

export interface MachineFormProps {
  initialData?: Machine
  onSubmit: (data: CreateMachineDTO | UpdateMachineDTO) => Promise<void> | void
  onCancel?: () => void
  isSubmitting?: boolean
  error?: string
}

export function MachineForm({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false,
  error,
}: MachineFormProps) {
  const { currentOrg, currentPlant } = useAuthStore()

  const [formData, setFormData] = useState<Partial<CreateMachineDTO>>({
    organization_id: initialData?.organization_id ?? currentOrg?.id,
    plant_id: initialData?.plant_id ?? currentPlant?.id,
    machine_code: initialData?.machine_code ?? '',
    machine_name: initialData?.machine_name ?? '',
    description: initialData?.description ?? '',
    work_center_id: initialData?.work_center_id ?? 1,
    status: initialData?.status ?? 'AVAILABLE',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    try {
      const schema = initialData ? updateMachineSchema : createMachineSchema
      schema.parse(formData)
      setErrors({})
      return true
    } catch (e) {
      if (e instanceof ZodError) {
        const newErrors: Record<string, string> = {}
        e.errors.forEach((err) => {
          const path = err.path.join('.')
          newErrors[path] = err.message
        })
        setErrors(newErrors)
      }
      return false
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    if (!initialData) {
      await onSubmit(formData as CreateMachineDTO)
    } else {
      // For update mode, only send changed fields
      const updateData: UpdateMachineDTO = {}
      if (formData.machine_name !== initialData.machine_name) {
        updateData.machine_name = formData.machine_name
      }
      if (formData.description !== initialData.description) {
        updateData.description = formData.description
      }
      if (formData.work_center_id !== initialData.work_center_id) {
        updateData.work_center_id = formData.work_center_id
      }
      if (formData.status !== initialData.status) {
        updateData.status = formData.status
      }

      await onSubmit(updateData)
    }
  }

  const handleChange = (field: keyof CreateMachineDTO) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const value = e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="machine-form">
      {error && <div className="error-message">{error}</div>}

      <div className="form-group">
        <label htmlFor="machine_code">Machine Code</label>
        <input
          id="machine_code"
          type="text"
          value={formData.machine_code}
          onChange={handleChange('machine_code')}
          disabled={isSubmitting || !!initialData}
        />
        {errors.machine_code && (
          <span className="error">{errors.machine_code}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="machine_name">Machine Name</label>
        <input
          id="machine_name"
          type="text"
          value={formData.machine_name}
          onChange={handleChange('machine_name')}
          disabled={isSubmitting}
        />
        {errors.machine_name && (
          <span className="error">{errors.machine_name}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          value={formData.description}
          onChange={handleChange('description')}
          disabled={isSubmitting}
        />
        {errors.description && (
          <span className="error">{errors.description}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="status">Status</label>
        <select
          id="status"
          value={formData.status}
          onChange={handleChange('status')}
          disabled={isSubmitting}
        >
          <option value="AVAILABLE">AVAILABLE</option>
          <option value="RUNNING">RUNNING</option>
          <option value="IDLE">IDLE</option>
          <option value="DOWN">DOWN</option>
          <option value="SETUP">SETUP</option>
          <option value="MAINTENANCE">MAINTENANCE</option>
        </select>
        {errors.status && (
          <span className="error">{errors.status}</span>
        )}
      </div>

      <div className="form-actions">
        <button type="submit" disabled={isSubmitting}>
          {initialData ? 'Update' : 'Create'}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
